import unittest
from unittest.mock import patch

from fastapi import HTTPException

import main


class SuratTugasAccessTests(unittest.TestCase):
    def setUp(self):
        self.surat_tugas = {
            "id": 42,
            "status": "TERBIT",
            "tgl_berangkat": "2026-10-01",
            "tgl_kembali": "2026-10-02",
        }
        self.spd_rows = [
            {"id": 1, "pegawai_id": 10, "jumlah": 100},
            {"id": 2, "pegawai_id": 20, "jumlah": 200},
        ]

    def test_pegawai_detail_contains_only_their_spd_and_total(self):
        with patch.object(main, "q", side_effect=[self.surat_tugas, self.spd_rows]):
            result = main.std(
                42, {"role": "PEGAWAI", "pegawai_id": 20}
            )

        self.assertEqual([row["id"] for row in result["spd"]], [2])
        self.assertEqual(result["total"], 200)

    def test_pegawai_cannot_open_another_employees_surat_tugas(self):
        with patch.object(main, "q", side_effect=[self.surat_tugas, self.spd_rows]):
            with self.assertRaises(HTTPException) as error:
                main.std(42, {"role": "PEGAWAI", "pegawai_id": 30})

        self.assertEqual(error.exception.status_code, 403)

    def test_non_pegawai_roles_keep_all_spd(self):
        with patch.object(main, "q", side_effect=[self.surat_tugas, self.spd_rows]):
            result = main.std(42, {"role": "PPK"})

        self.assertEqual([row["id"] for row in result["spd"]], [1, 2])
        self.assertEqual(result["total"], 300)

    def test_pegawai_list_only_aggregates_their_own_names(self):
        with patch.object(main, "q", return_value=[]) as query:
            result = main.stl(u={"role": "PEGAWAI", "pegawai_id": 20})

        sql, params = query.call_args.args
        self.assertIn("array_agg(p.nama order by p.urutan)", sql)
        self.assertIn("and p.pegawai_id=?", sql)
        self.assertEqual(params, [20, 20, 20, 20, 20])
        self.assertEqual(result, [])

    def test_surat_tugas_list_shows_newest_entries_last(self):
        with patch.object(main, "q", return_value=[]) as query:
            main.stl(u={"role": "ADMIN"})

        sql = query.call_args.args[0]
        self.assertIn("order by s.created_at,s.id", sql)
        self.assertNotIn("order by s.id desc", sql)


if __name__ == "__main__":
    unittest.main()
