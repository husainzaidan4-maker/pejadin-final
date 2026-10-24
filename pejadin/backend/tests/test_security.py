import unittest

from pejadin_docs.security import filter_spd_for_user, validate_token_secret


class ValidateTokenSecretTests(unittest.TestCase):
    def test_rejects_missing_or_short_secret(self):
        for secret in (None, "", "short"):
            with self.subTest(secret=secret):
                with self.assertRaises(RuntimeError):
                    validate_token_secret(secret)

    def test_rejects_placeholder_secret(self):
        with self.assertRaises(RuntimeError):
            validate_token_secret("ganti-rahasia-ini")

    def test_accepts_configured_secret(self):
        secret = "a" * 64
        self.assertEqual(validate_token_secret(secret), secret)

    def test_trims_configured_secret(self):
        secret = "a" * 64
        self.assertEqual(validate_token_secret(f"  {secret}  "), secret)


class FilterSpdForUserTests(unittest.TestCase):
    def test_pegawai_only_receives_their_own_spd(self):
        rows = [{"id": 1, "pegawai_id": 10}, {"id": 2, "pegawai_id": 20}]
        self.assertEqual(
            filter_spd_for_user(rows, {"role": "PEGAWAI", "pegawai_id": 20}),
            [{"id": 2, "pegawai_id": 20}],
        )

    def test_pegawai_without_linked_employee_receives_no_spd(self):
        rows = [{"id": 1, "pegawai_id": 10}]
        self.assertEqual(
            filter_spd_for_user(rows, {"role": "PEGAWAI", "pegawai_id": None}),
            [],
        )

    def test_other_roles_keep_all_spd_rows(self):
        rows = [{"id": 1, "pegawai_id": 10}, {"id": 2, "pegawai_id": 20}]
        self.assertEqual(
            filter_spd_for_user(rows, {"role": "PPK"}),
            rows,
        )


if __name__ == "__main__":
    unittest.main()
