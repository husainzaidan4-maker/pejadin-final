import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

import main


class WorkflowStateTests(unittest.IsolatedAsyncioTestCase):
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
                "method": "POST",
                "path": "/api/st/42/batalkan",
                "headers": [(b"content-type", b"application/json")],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("testclient", 123),
                "scheme": "http",
                "http_version": "1.1",
            },
            receive,
        )

    async def test_cannot_cancel_outside_diajukan(self):
        for status in ("DRAFT", "TERBIT", "SELESAI", "DIBATALKAN"):
            with self.subTest(status=status):
                with patch.object(main, "std", return_value={"status": status}):
                    with self.assertRaises(HTTPException) as error:
                        await main.aksi(
                            42,
                            "batalkan",
                            self.make_request({"alasan": "Uji"}),
                            {"role": "PPK"},
                        )
                self.assertEqual(error.exception.status_code, 409)

    async def test_ppk_can_cancel_diajukan_with_reason(self):
        with (
            patch.object(main, "std", return_value={"status": "DIAJUKAN"}),
            patch.object(main, "ex") as execute,
            patch.object(main, "touch"),
            patch.object(main, "log"),
            patch.object(main, "notify_st_transition"),
        ):
            result = await main.aksi(
                42,
                "batalkan",
                self.make_request({"alasan": "Perjalanan tidak jadi"}),
                {"role": "PPK", "username": "ppk"},
            )

        self.assertEqual(result, {"id": 42, "status": "DIBATALKAN"})
        execute.assert_called_once()

    async def test_operator_can_only_publish_a_draft(self):
        with patch.object(main, "std", return_value={"status": "DIAJUKAN"}):
            with self.assertRaises(HTTPException) as error:
                await main.aksi(
                    42,
                    "terbitkan",
                    self.make_request({"nomor": "ST/2026/42"}),
                    {"role": "OPERATOR"},
                )

        self.assertEqual(error.exception.status_code, 409)

    async def test_ppk_cannot_publish_a_draft_without_submission(self):
        with patch.object(main, "std", return_value={"status": "DRAFT"}):
            with self.assertRaises(HTTPException) as error:
                await main.aksi(
                    42,
                    "terbitkan",
                    self.make_request({"nomor": "ST/2026/42"}),
                    {"role": "PPK"},
                )

        self.assertEqual(error.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
