import json
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from starlette.requests import Request

import main


class SuratTugasDraftEditTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.body = {
            "maksud": "Rapat koordinasi",
            "nama_kegiatan": "Koordinasi",
            "asal": "Jakarta",
            "provinsi_asal": "DKI Jakarta",
            "tujuan": "Bandung",
            "provinsi": "Jawa Barat",
            "tgl_berangkat": "2026-12-07",
            "tgl_kembali": "2026-12-09",
            "tanggal_surat_tugas": "2026-12-01",
            "tgl_tanda_tangan": "2026-12-02",
            "nomor_bukti": "B/42",
            "uraian_kegiatan": "Rapat koordinasi pelaksanaan",
            "keterangan_laporan": "Kegiatan berjalan lancar",
            "alat": "Pesawat",
            "akun": "524111",
            "jenis": "UP",
        }
        self.current = {
            **self.body,
            "id": 42,
            "status": "DRAFT",
            "tgl_berangkat": date(2026, 12, 7),
            "tgl_kembali": date(2026, 12, 9),
            "tanggal_surat_tugas": date(2026, 12, 1),
            "tgl_tanda_tangan": date(2026, 12, 2),
        }
        self.operator = {"role": "OPERATOR", "username": "operator"}

    def make_request(self, body):
        raw_body = json.dumps(body).encode()
        sent = False

        async def receive():
            nonlocal sent
            if sent:
                return {"type": "http.disconnect"}
            sent = True
            return {"type": "http.request", "body": raw_body, "more_body": False}

        return Request(
            {
                "type": "http",
                "method": "PUT",
                "path": "/api/v1/st/42",
                "headers": [(b"content-type", b"application/json")],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("testclient", 123),
                "scheme": "http",
                "http_version": "1.1",
            },
            receive,
        )

    def make_pool(self, participants):
        current_cursor = MagicMock()
        current_cursor.fetchone.return_value = self.current
        participants_cursor = MagicMock()
        participants_cursor.fetchall.return_value = participants
        tariff_cursor = MagicMock()
        tariff_cursor.fetchone.return_value = {"id": 1}
        connection = MagicMock()
        connection.execute.side_effect = [
            current_cursor,
            participants_cursor,
            tariff_cursor,
            MagicMock(),
        ]
        pool = MagicMock()
        pool.connection.return_value.__enter__.return_value = connection
        return pool, connection

    async def test_updates_valid_draft_and_audits_before_and_after(self):
        pool, connection = self.make_pool([])
        body = {**self.body, "maksud": "  Rapat perubahan  "}

        with (
            patch.object(main, "pool", pool),
            patch.object(main, "q", return_value=[{"id": 1}]),
            patch.object(main, "log") as audit_log,
        ):
            result = await main.stu(42, self.make_request(body), self.operator)

        self.assertEqual(result, {"id": 42, "status": "DRAFT"})
        update = connection.execute.call_args_list[-1].args
        self.assertIn("update st set", update[0])
        self.assertIn("Rapat perubahan", update[1])
        audit_log.assert_called_once()
        self.assertEqual(audit_log.call_args.args[4]["before"]["maksud"], "Rapat koordinasi")
        self.assertEqual(audit_log.call_args.args[4]["after"]["maksud"], "Rapat perubahan")

    async def test_route_dates_cannot_change_until_participants_are_removed(self):
        pool, connection = self.make_pool([{"id": 5}])
        body = {**self.body, "tgl_berangkat": "2026-12-08", "tgl_kembali": "2026-12-10"}

        with (
            patch.object(main, "pool", pool),
            patch.object(main, "q", return_value=[{"id": 1}]),
        ):
            with self.assertRaises(HTTPException) as error:
                await main.stu(42, self.make_request(body), self.operator)

        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(connection.execute.call_count, 2)

    async def test_only_drafts_can_be_updated(self):
        self.current["status"] = "DIAJUKAN"
        pool, connection = self.make_pool([])

        with (
            patch.object(main, "pool", pool),
            patch.object(main, "q", return_value=[{"id": 1}]),
        ):
            with self.assertRaises(HTTPException) as error:
                await main.stu(42, self.make_request(self.body), self.operator)

        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(connection.execute.call_count, 1)


if __name__ == "__main__":
    unittest.main()
