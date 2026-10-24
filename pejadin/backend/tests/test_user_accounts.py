import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

import main


class UserAccountValidationTests(unittest.TestCase):
    def test_profile_exposes_safe_account_and_employee_details(self):
        account = {
            "id": 7,
            "username": "operator",
            "nama": "Operator",
            "role": "OPERATOR",
            "pegawai_id": 12,
            "aktif": 1,
            "created_at": "2026-01-02T03:04:05+00:00",
            "last_login": "2026-02-03T04:05:06+00:00",
            "password_hash": "never-return-this",
        }
        employee = {"nama": "Nama Pegawai", "nip": "123456789"}
        with patch.object(main, "q", return_value=employee):
            result = main.user_profile(account)

        self.assertEqual(result["username"], "operator")
        self.assertEqual(result["nama_pegawai"], "Nama Pegawai")
        self.assertEqual(result["pegawai_nip"], "123456789")
        self.assertEqual(result["created_at"], account["created_at"])
        self.assertNotIn("password_hash", result)

    def test_profile_without_employee_is_supported(self):
        result = main.user_profile(
            {"id": 8, "username": "admin", "role": "ADMIN", "pegawai_id": None}
        )

        self.assertIsNone(result["nama_pegawai"])
        self.assertIsNone(result["pegawai_nip"])

    def test_admin_account_list_includes_creation_time(self):
        with patch.object(main, "q", return_value=[]) as query:
            result = main.lst("users", {"role": "ADMIN"})

        self.assertEqual(result, [])
        self.assertIn("a.created_at", query.call_args.args[0])

    def test_pegawai_role_requires_a_linked_employee(self):
        with self.assertRaises(HTTPException) as error:
            main.validate_user_account(
                {"username": "pegawai.baru", "role": "PEGAWAI", "password": "password123"},
                require_password=True,
            )

        self.assertEqual(error.exception.status_code, 422)
        self.assertIn("wajib terhubung", error.exception.detail["error"]["message"])

    def test_valid_account_normalizes_optional_employee_and_username(self):
        result = main.validate_user_account(
            {
                "username": "  operator.baru ",
                "role": "OPERATOR",
                "pegawai_id": "",
                "password": "password123",
            },
            require_password=True,
        )

        self.assertEqual(result["username"], "operator.baru")
        self.assertIsNone(result["pegawai_id"])
        self.assertEqual(result["password"], "password123")

    def test_password_minimum_length_is_enforced(self):
        with self.assertRaises(HTTPException) as error:
            main.validate_user_account(
                {"username": "operator", "role": "OPERATOR", "password": "short"},
                require_password=True,
            )

        self.assertEqual(error.exception.status_code, 422)

    def test_username_format_is_enforced(self):
        with self.assertRaises(HTTPException) as error:
            main.validate_user_account(
                {"username": "operator user", "role": "OPERATOR", "password": "password123"},
                require_password=True,
            )

        self.assertEqual(error.exception.status_code, 422)

    def test_admin_cannot_deactivate_own_account(self):
        connection = MagicMock()
        connection.execute.side_effect = [
            MagicMock(),
            MagicMock(
                fetchone=MagicMock(
                    return_value={
                        "id": 7,
                        "username": "admin",
                        "nama": "Admin",
                        "role": "ADMIN",
                        "pegawai_id": None,
                        "aktif": 1,
                        "last_login": None,
                    }
                )
            ),
        ]
        pool = MagicMock()
        pool.connection.return_value.__enter__.return_value = connection

        with patch.object(main, "pool", pool):
            with self.assertRaises(HTTPException) as error:
                main.save_user_account(
                    {"username": "admin", "role": "ADMIN", "aktif": 0},
                    {"id": 7, "role": "ADMIN"},
                    existing_id=7,
                )

        self.assertEqual(error.exception.status_code, 409)
        self.assertIn("akun sendiri", error.exception.detail["error"]["message"])

    def test_last_active_admin_cannot_be_demoted(self):
        connection = MagicMock()
        connection.execute.side_effect = [
            MagicMock(),
            MagicMock(
                fetchone=MagicMock(
                    return_value={
                        "id": 7,
                        "username": "admin",
                        "nama": "Admin",
                        "role": "ADMIN",
                        "pegawai_id": None,
                        "aktif": 1,
                        "last_login": None,
                    }
                )
            ),
            MagicMock(fetchone=MagicMock(return_value=None)),
            MagicMock(fetchone=MagicMock(return_value={"jumlah": 0})),
        ]
        pool = MagicMock()
        pool.connection.return_value.__enter__.return_value = connection

        with patch.object(main, "pool", pool):
            with self.assertRaises(HTTPException) as error:
                main.save_user_account(
                    {"username": "admin", "role": "OPERATOR", "pegawai_id": None},
                    {"id": 8, "role": "ADMIN"},
                    existing_id=7,
                )

        self.assertEqual(error.exception.status_code, 409)
        self.assertIn("admin aktif terakhir", error.exception.detail["error"]["message"])

    def test_created_account_is_audited_without_password_data(self):
        connection = MagicMock()
        duplicate_check = MagicMock(fetchone=MagicMock(return_value=None))
        inserted = MagicMock(fetchone=MagicMock(return_value={"id": 31}))
        connection.execute.side_effect = [MagicMock(), duplicate_check, inserted]
        pool = MagicMock()
        pool.connection.return_value.__enter__.return_value = connection

        with (
            patch.object(main, "pool", pool),
            patch.object(main, "log") as audit_log,
        ):
            result = main.save_user_account(
                {
                    "username": "operator.baru",
                    "password": "password123",
                    "role": "OPERATOR",
                    "pegawai_id": None,
                },
                {"id": 7, "role": "ADMIN"},
            )

        self.assertEqual(result, {"id": 31})
        self.assertEqual(audit_log.call_args.args[1:4], ("CREATE", "users", 31))
        self.assertNotIn("password", str(audit_log.call_args.args[4]))
        self.assertNotIn("password_hash", str(audit_log.call_args.args[4]))


if __name__ == "__main__":
    unittest.main()
