import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

import main


class RoleSeparationTests(unittest.IsolatedAsyncioTestCase):
    def make_request(self, body, path):
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

    def test_strict_role_dependency_does_not_allow_admin_bypass(self):
        operator_only = main.need_role("OPERATOR")
        with self.assertRaises(HTTPException) as error:
            operator_only({"role": "ADMIN"})
        self.assertEqual(error.exception.status_code, 403)

    async def test_admin_cannot_advance_workflow_actions(self):
        cases = (
            ("ajukan", "DRAFT"),
            ("terbitkan", "DRAFT"),
            ("terbitkan", "DIAJUKAN"),
        )
        for action, status in cases:
            with self.subTest(action=action):
                with patch.object(main, "std", return_value={"status": status}):
                    with self.assertRaises(HTTPException) as error:
                        await main.aksi(
                            42,
                            action,
                            self.make_request(
                                {"nomor": "ST/2026/42"},
                                f"/api/st/42/{action}",
                            ),
                            {"role": "ADMIN"},
                        )
                self.assertEqual(error.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
