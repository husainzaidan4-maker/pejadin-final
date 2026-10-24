import asyncio
import json
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

import main


class SuratTugasInputValidationTests(unittest.TestCase):
    def setUp(self):
        self.body = {
            "nama_kegiatan": "Koordinasi kegiatan",
            "maksud": "Rapat koordinasi",
            "asal": "Jakarta",
            "provinsi_asal": "DKI Jakarta",
            "tujuan": "Bandung",
            "provinsi": "Jawa Barat",
            "tgl_berangkat": "2026-12-07",
            "tgl_kembali": "2026-12-09",
            "tanggal_surat_tugas": "2026-12-01",
            "tgl_tanda_tangan": "2026-12-02",
            "jenis": "UP",
            "alat": "Pesawat",
            "akun": "524111",
            "nomor_bukti": "B/42",
            "uraian_kegiatan": "Rapat koordinasi pelaksanaan",
            "keterangan_laporan": "Kegiatan berjalan lancar",
        }
        self.operator = {"role": "OPERATOR", "username": "operator"}

    def make_request(self, body, method="POST", path="/api/st"):
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
                "method": method,
                "path": path,
                "headers": [(b"content-type", b"application/json")],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("testclient", 123),
                "scheme": "http",
                "http_version": "1.1",
            },
            receive,
        )

    def test_create_rejects_invalid_document_fields(self):
        cases = (
            ({"nama_kegiatan": " "}, "422"),
            ({"maksud": "  "}, "422"),
            ({"tujuan": ""}, "422"),
            ({"nomor_bukti": ""}, "422"),
            ({"uraian_kegiatan": ""}, "422"),
            ({"keterangan_laporan": ""}, "422"),
            ({"provinsi_asal": ""}, "422"),
            ({"jenis": "cash"}, "422"),
            ({"tanggal_surat_tugas": "2026-12-08"}, "V1"),
            ({"tgl_tanda_tangan": "2026-12-08"}, "V1"),
        )
        for changes, expected_code in cases:
            with self.subTest(changes=changes):
                body = {**self.body, **changes}
                with patch.object(main, "q", return_value=[{"id": 1}]):
                    with self.assertRaises(HTTPException) as error:
                        asyncio.run(main.stc(self.make_request(body), self.operator))
                self.assertEqual(error.exception.detail["error"]["code"], expected_code)

    def test_validation_error_uses_http_422(self):
        with self.assertRaises(HTTPException) as error:
            main.err("422", "Data tidak valid")

        self.assertEqual(error.exception.status_code, 422)

    def test_validation_codes_default_to_http_422(self):
        with self.assertRaises(HTTPException) as error:
            main.err("V1", "Durasi tidak sesuai")

        self.assertEqual(error.exception.status_code, 422)

    def test_api_exception_handler_returns_documented_error_shape(self):
        request = self.make_request({})
        error = HTTPException(
            422,
            {"error": {"code": "V1", "message": "Durasi tidak sesuai"}},
        )

        response = asyncio.run(main.api_exception_handler(request, error))

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            json.loads(response.body),
            {"error": {"code": "V1", "message": "Durasi tidak sesuai"}},
        )

    def test_request_validation_handler_returns_documented_error_shape(self):
        request = self.make_request({})
        error = RequestValidationError([])

        response = asyncio.run(
            main.request_validation_exception_handler(request, error)
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            json.loads(response.body),
            {"error": {"code": "422", "message": "Parameter permintaan tidak valid"}},
        )

    def test_create_normalizes_valid_document_fields(self):
        body = {
            **self.body,
            "nama_kegiatan": "  Koordinasi kegiatan  ",
            "maksud": "  Rapat koordinasi  ",
            "tujuan": " Bandung ",
            "jenis": " up ",
        }
        with (
            patch.object(main, "q", return_value=[{"id": 1}]),
            patch.object(main, "ex", return_value=42) as insert,
            patch.object(main, "touch"),
            patch.object(main, "log"),
            patch.object(main, "notify_st_created"),
        ):
            result = asyncio.run(main.stc(self.make_request(body), self.operator))

        self.assertEqual(result, {"id": 42, "status": "DRAFT"})
        columns = insert.call_args.args[0].split("(", 1)[1].split(")", 1)[0].split(",")
        values = insert.call_args.args[1]
        saved = dict(zip(columns, values))
        self.assertEqual(saved["maksud"], "Rapat koordinasi")
        self.assertEqual(saved["nama_kegiatan"], "Koordinasi kegiatan")
        self.assertEqual(saved["tujuan"], "Bandung")
        self.assertEqual(saved["provinsi_asal"], "DKI Jakarta")
        self.assertEqual(saved["jenis"], "UP")

    def test_create_allows_dates_to_be_left_for_handwriting(self):
        body = {**self.body, "tanggal_surat_tugas": "", "tgl_tanda_tangan": None}
        with (
            patch.object(main, "q", return_value=[{"id": 1}]),
            patch.object(main, "ex", return_value=42) as insert,
            patch.object(main, "touch"),
            patch.object(main, "log"),
            patch.object(main, "notify_st_created"),
        ):
            result = asyncio.run(main.stc(self.make_request(body), self.operator))

        self.assertEqual(result, {"id": 42, "status": "DRAFT"})
        columns = insert.call_args.args[0].split("(", 1)[1].split(")", 1)[0].split(",")
        values = insert.call_args.args[1]
        saved = dict(zip(columns, values))
        self.assertIsNone(saved["tanggal_surat_tugas"])
        self.assertIsNone(saved["tgl_tanda_tangan"])

    def test_pdf_data_preparation_accepts_dates_left_blank(self):
        surat_tugas = {
            "nomor": "ST/2026/42",
            "status": "TERBIT",
            "tgl_berangkat": "2026-12-07",
            "tgl_kembali": "2026-12-09",
            "tanggal_surat_tugas": None,
            "tgl_tanda_tangan": None,
        }
        with patch.object(
            main,
            "q",
            side_effect=[[{"k": "kota_kedudukan", "v": "Jakarta"}], []],
        ):
            _, _, pdf_data, participants = main.siapkan_data_pdf(surat_tugas, [])

        self.assertIsNone(pdf_data.tanggal_surat_tugas)
        self.assertIsNone(pdf_data.tgl_tanda_tangan)
        self.assertEqual(participants, [])

    def test_publish_rejects_legacy_draft_with_missing_required_fields(self):
        locked_st = {
            "id": 42,
            "status": "DIAJUKAN",
            "tgl_berangkat": "2026-12-07",
            "maksud": "",
            "tujuan": "Bandung",
            "jenis": "UP",
            "tanggal_surat_tugas": "2026-12-01",
            "tgl_tanda_tangan": "2026-12-02",
        }
        cursor = MagicMock()
        cursor.fetchone.return_value = locked_st
        connection = MagicMock()
        connection.execute.return_value = cursor
        pool = MagicMock()
        pool.connection.return_value.__enter__.return_value = connection

        with (
            patch.object(main, "std", return_value={"status": "DIAJUKAN"}),
            patch.object(main, "pool", pool),
        ):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(
                    main.aksi(
                        42,
                        "terbitkan",
                        self.make_request(
                            {"nomor": "ST/2026/42"},
                            path="/api/st/42/terbitkan",
                        ),
                        {"role": "PPK", "nama": "PPK"},
                    )
                )

        self.assertEqual(error.exception.detail["error"]["code"], "422")


if __name__ == "__main__":
    unittest.main()
