import unittest
from unittest.mock import patch

import main


class LegacyDocumentHtmlTests(unittest.TestCase):
    def test_dynamic_document_values_are_html_escaped(self):
        payload = '<img src=x onerror="alert(1)">'
        surat_tugas = {
            "id": 42,
            "status": "TERBIT",
            "nomor": payload,
            "maksud": payload,
            "tujuan": "Jakarta",
            "provinsi": "DKI Jakarta",
            "tgl_berangkat": "2026-10-01",
            "tgl_kembali": "2026-10-02",
            "lama": 2,
            "spd": [{
                "urutan": 1,
                "nama": payload,
                "nip": "001234",
                "jabatan": "Pelaksana",
                "jumlah": 100,
            }],
        }
        satker = {
            "nama_kementerian": "Kementerian",
            "nama_ditjen": "Direktorat",
            "nama_satker": "Satuan Kerja",
            "alamat": "Jakarta",
            "kota": "Jakarta",
        }
        pejabat = [{
            "peran": "SEKDITJEN",
            "jabatan": "Pejabat",
            "nama": "Penanda tangan",
            "nip": "000123",
        }]

        with (
            patch.object(main, "std", return_value=surat_tugas),
            patch.object(main, "gs", return_value=satker),
            patch.object(main, "q", side_effect=[pejabat, [{"teks": payload}]]),
            patch.object(main, "log"),
            patch.object(main, "ex"),
        ):
            response = main.doc(42, "st", {"id": 7, "role": "PPK"})

        self.assertNotIn(payload, response)
        self.assertIn("&lt;img src=x onerror=&quot;alert(1)&quot;&gt;", response)
        self.assertIn("<script>print()</script>", response)

    def test_html_escape_encodes_markup_and_attribute_quotes(self):
        self.assertEqual(
            main.html_escape('<b title="safe">Jumlah & lain</b>'),
            "&lt;b title=&quot;safe&quot;&gt;Jumlah &amp; lain&lt;/b&gt;",
        )


if __name__ == "__main__":
    unittest.main()
