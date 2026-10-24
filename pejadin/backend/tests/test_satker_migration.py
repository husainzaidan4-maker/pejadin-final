import asyncio
import datetime as dt
import json
import unittest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from starlette.requests import Request

import main
from pejadin_docs.satker_migration import (
    SATKER_PROFILE_FIELDS,
    SATKER_TRANSITION_YEAR,
    migrate_legacy_satker,
    sync_legacy_satker,
)


class SatkerMigrationTests(unittest.TestCase):
    def make_request(self, body):
        sent = False

        async def receive():
            nonlocal sent
            if sent:
                return {"type": "http.disconnect"}
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        return Request(
            {
                "type": "http",
                "method": "PUT",
                "path": "/api/ref/satker",
                "headers": [(b"content-type", b"application/json")],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("testclient", 123),
                "scheme": "http",
                "http_version": "1.1",
            },
            receive,
        )

    def test_backfill_is_year_scoped_and_idempotent(self):
        connection = MagicMock()

        migrate_legacy_satker(connection)

        create_sql = connection.execute.call_args_list[0].args[0]
        migration_sql = [
            entry.args[0] for entry in connection.execute.call_args_list
        ]
        backfill_call = connection.execute.call_args_list[-1]
        backfill_sql, params = backfill_call.args
        self.assertIn("create table if not exists satker_tahunan", create_sql)
        self.assertIn("tahun_anggaran int primary key", create_sql)
        for field in SATKER_PROFILE_FIELDS:
            self.assertIn(field, create_sql)
            if field != "tanggal_dipa":
                self.assertIn(f"max(v) filter (where k = '{field}')", backfill_sql)
        self.assertIn("tanggal_dipa date", create_sql)
        self.assertIn("kode_akun_belanja varchar(10)", create_sql)
        self.assertIn(
            "nullif(max(v) filter (where k = 'tanggal_dipa'), '')::date",
            backfill_sql,
        )
        self.assertTrue(
            any("add column if not exists tanggal_dipa date" in sql for sql in migration_sql)
        )
        self.assertTrue(
            any(
                "add column if not exists kode_akun_belanja varchar(10)" in sql
                for sql in migration_sql
            )
        )
        self.assertIn("having count(*) > 0", backfill_sql)
        self.assertIn("on conflict(tahun_anggaran) do nothing", backfill_sql)
        self.assertEqual(params, (SATKER_TRANSITION_YEAR,))

    def test_legacy_updates_sync_only_known_profile_fields(self):
        connection = MagicMock()
        values = {
            "nama_satker": "Satker Baru",
            "kota_kedudukan": "Bandung",
            "tanggal_dipa": "2026-01-15",
            "field_lama_tambahan": "nilai lama",
        }

        sync_legacy_satker(connection, values)

        sql, params = connection.execute.call_args.args
        self.assertIn("on conflict(tahun_anggaran) do update set", sql)
        self.assertIn("nama_satker=excluded.nama_satker", sql)
        self.assertIn("kota_kedudukan=excluded.kota_kedudukan", sql)
        self.assertIn("tanggal_dipa=excluded.tanggal_dipa", sql)
        self.assertNotIn("field_lama_tambahan", sql)
        self.assertEqual(
            params,
            (SATKER_TRANSITION_YEAR, "Satker Baru", dt.date(2026, 1, 15), "Bandung"),
        )

    def test_legacy_update_rejects_invalid_dipa_date(self):
        connection = MagicMock()

        with self.assertRaises(ValueError):
            sync_legacy_satker(connection, {"tanggal_dipa": "15/01/2026"})

        connection.execute.assert_not_called()

    def test_legacy_update_without_profile_fields_does_not_write_profile(self):
        connection = MagicMock()

        sync_legacy_satker(connection, {"field_lama_tambahan": "nilai"})

        connection.execute.assert_not_called()

    def test_legacy_api_updates_both_representations_in_one_transaction(self):
        request = self.make_request(
            json.dumps(
                {"nama_satker": "Satker Baru", "tanggal_dipa": "2026-01-15"}
            ).encode()
        )
        connection = MagicMock()
        pool = MagicMock()
        pool.connection.return_value.__enter__.return_value = connection
        user = {"id": 1, "username": "operator", "role": "OPERATOR"}

        with (
            patch.object(main, "pool", pool),
            patch.object(main, "log") as audit_log,
        ):
            response = asyncio.run(main.ps(request, user))

        statements = [call.args[0] for call in connection.execute.call_args_list]
        self.assertEqual(response, {"ok": 1})
        self.assertTrue(any("insert into satker(k,v)" in sql for sql in statements))
        self.assertTrue(any("insert into satker_tahunan" in sql for sql in statements))
        profile_write = next(
            call for call in connection.execute.call_args_list
            if "insert into satker_tahunan" in call.args[0]
        )
        self.assertIn(dt.date(2026, 1, 15), profile_write.args[1])
        connection.transaction.assert_called_once()
        audit_log.assert_called_once_with(
            user,
            "UPDATE",
            "satker",
            0,
            {
                "before": {"nama_satker": None, "tanggal_dipa": None},
                "after": {
                    "nama_satker": "Satker Baru",
                    "tanggal_dipa": dt.date(2026, 1, 15),
                },
            },
        )

    def test_legacy_api_rejects_invalid_dipa_date_before_writing(self):
        connection = MagicMock()
        pool = MagicMock()
        pool.connection.return_value.__enter__.return_value = connection

        with (
            patch.object(main, "pool", pool),
            patch.object(main, "log"),
        ):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(
                    main.ps(
                        self.make_request(
                            b'{"tanggal_dipa":"15/01/2026"}'
                        ),
                        {"id": 1, "username": "operator", "role": "OPERATOR"},
                    )
                )

        self.assertEqual(raised.exception.status_code, 422)
        connection.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
