import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from pypdf import PdfReader

from pejadin_docs.pdf_rincian_kuitansi import buat_pdf_kuitansi, buat_pdf_rincian


class RincianSignatureTests(unittest.TestCase):
    def test_rincian_pdf_includes_ppk_bendahara_and_pegawai_signatures(self):
        surat_tugas = SimpleNamespace(
            nomor_surat_tugas="ST/2026/42",
            tgl_tanda_tangan=SimpleNamespace(day=10, month=10, year=2026),
            asal="Jakarta",
            tujuan="Bandung",
        )
        spd_hasil = SimpleNamespace(
            pegawai=SimpleNamespace(nama="Pegawai Contoh", nip_nrp="001234"),
            transport_tiket=0,
            taksi=0,
            hari=1,
            tarif_uang_harian=100,
            uang_harian=100,
            malam_inap=0,
            tarif_inap=0,
            uang_penginapan=0,
            tarif_representasi=0,
            uang_representasi=0,
            biaya_lain=0,
            jumlah=100,
            flag_lebih_sbm=False,
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "rincian.pdf"
            buat_pdf_rincian(
                str(output),
                {"kota_kedudukan": "Jakarta"},
                {"nama": "Bendahara Contoh", "nip": "000111"},
                {"nama": "PPK Contoh", "nip": "000222"},
                surat_tugas,
                spd_hasil,
            )
            text = "\n".join(page.extract_text() or "" for page in PdfReader(output).pages)

        for expected in (
            "Bendahara Pengeluaran",
            "Pejabat Pembuat Komitmen",
            "Pelaksana Perjalanan Dinas",
            "Bendahara Contoh",
            "PPK Contoh",
            "Pegawai Contoh",
            "NIP. 000222",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_rincian_pdf_shows_sbm_capped_lodging_and_actual_bill(self):
        surat_tugas = SimpleNamespace(
            nomor_surat_tugas="ST/2026/42",
            tgl_tanda_tangan=SimpleNamespace(day=10, month=10, year=2026),
            asal="Jakarta",
            tujuan="Bandung",
        )
        spd_hasil = SimpleNamespace(
            pegawai=SimpleNamespace(nama="Pegawai Contoh", nip_nrp="001234"),
            transport_tiket=0,
            taksi=0,
            hari=3,
            tarif_uang_harian=100,
            uang_harian=300,
            malam_inap=2,
            tarif_inap=9000,
            batas_sbm_inap=1366,
            uang_penginapan=2732,
            tarif_representasi=0,
            uang_representasi=0,
            biaya_lain=0,
            jumlah=3042,
            flag_lebih_sbm=True,
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "rincian.pdf"
            buat_pdf_rincian(
                str(output),
                {"kota_kedudukan": "Jakarta"},
                {"nama": "Bendahara Contoh", "nip": "000111"},
                {"nama": "PPK Contoh", "nip": "000222"},
                surat_tugas,
                spd_hasil,
            )
            text = "\n".join(page.extract_text() or "" for page in PdfReader(output).pages)

        self.assertIn("Rp 9.000", text)
        self.assertIn("Rp 1.366", text)
        self.assertIn("Rp 2.732", text)
        self.assertIn("dibayar dibatasi", text)

    def test_kuitansi_includes_bendahara_ppk_and_existing_adm_signer(self):
        surat_tugas = SimpleNamespace(
            tahun_anggaran=2026,
            akun_anggaran="524111",
            maksud_perjalanan="Rapat koordinasi",
            tujuan="Bandung",
            nomor_surat_tugas="ST/2026/42",
            tgl_tanda_tangan=SimpleNamespace(day=10, month=10, year=2026),
            asal="Jakarta",
        )
        satker = {
            "nama_kementerian": "Kementerian",
            "nama_ditjen": "Direktorat",
            "nama_satker_panjang": "Satuan Kerja",
            "alamat": "Jakarta",
            "tahun_anggaran": 2026,
            "kota_kedudukan": "Jakarta",
            "nama_satker": "Satuan Kerja",
        }
        pejabat_ppk = {"nama": "PPK Contoh", "nip": "000222"}
        pejabat_bendahara = {
            "nama": "Bendahara Contoh",
            "nip": "000111",
        }
        pejabat_pelaksana_adm = {
            "jabatan_lengkap": "Penerima Contoh",
            "nama": "Penerima Kuitansi",
            "nip": "000333",
        }

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "kuitansi.pdf"
            buat_pdf_kuitansi(
                str(output),
                satker,
                pejabat_ppk,
                pejabat_bendahara,
                pejabat_pelaksana_adm,
                surat_tugas,
                150000,
                "B/42",
            )
            text = "\n".join(page.extract_text() or "" for page in PdfReader(output).pages)

        for expected in (
            "Bendahara Pengeluaran",
            "Bendahara Contoh",
            "PPK Contoh",
            "Penerima Kuitansi",
            "NIP. 000111",
            "NIP. 000222",
            "NIP. 000333",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
