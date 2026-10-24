import unittest

from main import validasi_pilihan_pdf


class ValidasiPilihanPdfTests(unittest.TestCase):
    def test_accepts_unique_documents_and_both_output_formats(self):
        for output_format in ("zip", "pdf"):
            with self.subTest(output_format=output_format):
                self.assertEqual(
                    validasi_pilihan_pdf(["st", "spd"], output_format),
                    ["st", "spd"],
                )

    def test_rejects_empty_or_non_list_document_selection(self):
        for selection in (None, [], "st"):
            with self.subTest(selection=selection):
                with self.assertRaises(ValueError):
                    validasi_pilihan_pdf(selection, "zip")

    def test_rejects_unknown_duplicate_and_complete_package_types(self):
        for selection in (["unknown"], ["st", "st"], ["lengkap"]):
            with self.subTest(selection=selection):
                with self.assertRaises(ValueError):
                    validasi_pilihan_pdf(selection, "pdf")

    def test_rejects_invalid_output_format(self):
        with self.assertRaises(ValueError):
            validasi_pilihan_pdf(["st"], "docx")


if __name__ == "__main__":
    unittest.main()
