import unittest
from unittest.mock import MagicMock

from pejadin_docs.satker_migration import ensure_spd_pegawai_foreign_key


class SpdEmployeeForeignKeyTests(unittest.TestCase):
    def test_adds_not_valid_foreign_key_when_no_existing_orphans(self):
        connection = MagicMock()
        connection.execute.return_value.fetchone.return_value = {"total": 0}

        result = ensure_spd_pegawai_foreign_key(connection)

        self.assertEqual(result, 0)
        statements = [call.args[0] for call in connection.execute.call_args_list]
        self.assertIn("left join pegawai g on g.id=p.pegawai_id", statements[0])
        constraint_sql = statements[1]
        self.assertIn(
            "foreign key (pegawai_id) references pegawai(id) not valid",
            constraint_sql,
        )
        self.assertIn("conrelid='spd'::regclass", constraint_sql)

    def test_adds_fk_and_reports_existing_orphaned_rows(self):
        connection = MagicMock()
        connection.execute.return_value.fetchone.return_value = {"total": 2}

        result = ensure_spd_pegawai_foreign_key(connection)

        self.assertEqual(result, 2)
        self.assertEqual(connection.execute.call_count, 2)
        self.assertIn(
            "foreign key (pegawai_id) references pegawai(id) not valid",
            connection.execute.call_args.args[0],
        )


if __name__ == "__main__":
    unittest.main()
