import json
import unittest
from datetime import timezone
from unittest.mock import MagicMock, patch

import main


class AuditLoggingTests(unittest.TestCase):
    def test_writes_both_audit_rows_in_one_transaction(self):
        connection = MagicMock()
        pool = MagicMock()
        pool.connection.return_value.__enter__.return_value = connection
        user = {"id": 7, "username": "auditor"}

        with patch.object(main, "pool", pool), patch.object(main, "NOW", return_value="now"):
            main.log(user, "TERBITKAN", "st", 42, "ST/2026/42")

        connection.transaction.assert_called_once_with()
        self.assertEqual(connection.execute.call_count, 2)
        self.assertIn("insert into audit(", connection.execute.call_args_list[0].args[0])
        self.assertIn("insert into audit_log(", connection.execute.call_args_list[1].args[0])

    def test_stores_structured_before_and_after_values_without_secrets(self):
        connection = MagicMock()
        pool = MagicMock()
        pool.connection.return_value.__enter__.return_value = connection
        detail = {
            "before": {
                "status": "DRAFT",
                "rekening_bendahara": "1234567890",
                "nip": "123456789012345678",
            },
            "after": {
                "status": "DIAJUKAN",
                "password_hash": "must-not-be-audited",
            },
        }

        with patch.object(main, "pool", pool):
            main.log(
                {"id": 7, "username": "auditor"},
                "UPDATE",
                "st",
                42,
                detail,
            )

        audit_detail = connection.execute.call_args_list[0].args[1][4]
        audit_log_detail = json.loads(connection.execute.call_args_list[1].args[1][4])
        expected = {
            "before": {
                "status": "DRAFT",
                "rekening_bendahara": "***7890",
                "nip": "***5678",
            },
            "after": {"status": "DIAJUKAN"},
        }
        self.assertEqual(json.loads(audit_detail), expected)
        self.assertEqual(audit_log_detail, expected)

    def test_audit_timestamp_is_timezone_aware_utc(self):
        self.assertEqual(main.NOW().utcoffset(), timezone.utc.utcoffset(None))

    def test_audit_log_write_failure_is_not_suppressed(self):
        connection = MagicMock()
        connection.execute.side_effect = [None, RuntimeError("audit_log unavailable")]
        pool = MagicMock()
        pool.connection.return_value.__enter__.return_value = connection

        with patch.object(main, "pool", pool):
            with self.assertRaisesRegex(RuntimeError, "audit_log unavailable"):
                main.log({"id": 7, "username": "auditor"}, "CETAK", "st", 42, "spd")

        connection.transaction.assert_called_once_with()
        self.assertEqual(connection.execute.call_count, 2)


if __name__ == "__main__":
    unittest.main()
