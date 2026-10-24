import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from pypdf import PdfReader

from pejadin_docs.pdf_common import fmt_tgl_tulis_tangan
from pejadin_docs.pdf_st import buat_pdf_st, buat_pdf_st_lampiran


class HandwrittenDatePdfTests(unittest.TestCase):
    def test_existing_dates_keep_their_indonesian_format(self):
        self.assertEqual(fmt_tgl_tulis_tangan(date(2026, 12, 7)), "7 Desember 2026")

    def test_st_and_attachment_show_handwriting_lines_when_dates_are_empty(self):
        surat_tugas = SimpleNamespace(
            nomor_surat_tugas="ST/2026/42",
            tanggal_surat_tugas=None,
            tgl_tanda_tangan=None,
            tgl_berangkat=date(2026, 12, 7),
            tgl_kembali=date(2026, 12, 9),
            maksud_perjalanan="Rapat koordinasi",
            tujuan="Bandung",
            nama_kegiatan=None,
            akun_anggaran="524111",
        )
        pejabat = {
            "SEKDITJEN": {
                "jabatan_lengkap": "Sekretaris Direktorat Jenderal",
                "nama": "Sekditjen Contoh",
            },
            "PPK": {"nama": "PPK Contoh"},
            "KABAG": {"nama": "Kabag Contoh"},
        }
        satker = {"kota_kedudukan": "Jakarta", "nama_satker": "Setditjen SDA"}
        placeholder = "...................................."

        with tempfile.TemporaryDirectory() as directory:
            st_path = Path(directory) / "st.pdf"
            attachment_path = Path(directory) / "attachment.pdf"
            buat_pdf_st(str(st_path), satker, pejabat, [], surat_tugas)
            buat_pdf_st_lampiran(str(attachment_path), satker, pejabat, surat_tugas, [])
            st_text = "\n".join(page.extract_text() or "" for page in PdfReader(st_path).pages)
            attachment_text = "\n".join(
                page.extract_text() or "" for page in PdfReader(attachment_path).pages
            )

        self.assertIn(f"Jakarta, {placeholder}", st_text)
        self.assertIn(f"TANGGAL : {placeholder}", attachment_text)


if __name__ == "__main__":
    unittest.main()
