import unittest
from unittest.mock import patch

import main


class NotificationTransitionTests(unittest.TestCase):
    @patch.object(main, "pool")
    def test_cancellation_notifies_the_originating_operator(self, pool):
        connection = pool.connection.return_value.__enter__.return_value
        connection.execute.return_value.fetchall.return_value = [{"id": 8}, {"id": 9}]

        main.notify_st_transition(
            {"id": 8, "username": "ppk", "nama": "PPK"},
            "batalkan",
            42,
            {"nomor": "ST/2026/42", "dibuat_oleh": "operator"},
        )

        connection.execute.assert_called_once()
        self.assertEqual(
            connection.execute.call_args.args[1],
            (["OPERATOR"], "operator"),
        )
        connection.executemany.assert_called_once()
        self.assertEqual(
            connection.executemany.call_args.args[1],
            [
                (
                    9,
                    42,
                    "BATALKAN",
                    "Surat Tugas dibatalkan",
                    "ST/2026/42 dibatalkan. Alasan: -",
                )
            ],
        )

    @patch.object(main, "pool")
    def test_publication_notifies_stakeholders_and_originating_operator(self, pool):
        connection = pool.connection.return_value.__enter__.return_value
        connection.execute.return_value.fetchall.return_value = [
            {"id": 9, "role": "OPERATOR"},
            {"id": 10, "role": "PPK"},
            {"id": 11, "role": "BENDAHARA"},
            {"id": 8, "role": "PPK"},
        ]

        main.notify_st_transition(
            {"id": 8, "username": "ppk", "nama": "PPK"},
            "terbitkan",
            42,
            {"nomor": "ST/2026/42", "dibuat_oleh": "operator"},
        )

        self.assertEqual(
            connection.execute.call_args.args[1],
            (["OPERATOR", "PPK", "BENDAHARA"], "operator"),
        )
        self.assertEqual(
            connection.executemany.call_args.args[1],
            [
                (
                    9,
                    42,
                    "TERBITKAN",
                    "Surat Tugas diterbitkan",
                    "ST/2026/42 telah diterbitkan.",
                ),
                (
                    10,
                    42,
                    "TERBITKAN",
                    "Surat Tugas diterbitkan",
                    "ST/2026/42 telah diterbitkan.",
                ),
                (
                    11,
                    42,
                    "TERBITKAN",
                    "Surat Tugas diterbitkan",
                    "ST/2026/42 telah diterbitkan.",
                ),
            ],
        )

    @patch.object(main, "pool")
    def test_draft_creation_notifies_the_creating_operator(self, pool):
        connection = pool.connection.return_value.__enter__.return_value

        main.notify_st_created(
            {"id": 8},
            42,
            {"nama_kegiatan": "Koordinasi kegiatan"},
        )

        connection.execute.assert_called_once_with(
            "insert into notifications(user_id,st_id,action,title,message) "
            "values(%s,%s,%s,%s,%s)",
            (
                8,
                42,
                "DRAFT_DIBUAT",
                "Draft Surat Tugas dibuat",
                "Draft Koordinasi kegiatan berhasil dibuat dan siap dilengkapi.",
            ),
        )

    @patch.object(main, "pool")
    def test_unknown_transition_does_not_open_database_connection(self, pool):
        main.notify_st_transition({"id": 1}, "perbarui", 42, {})

        pool.connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
