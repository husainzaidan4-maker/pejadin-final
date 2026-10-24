import unittest
from datetime import date
import json
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

import main
from pejadin_docs.business_rules import (
    Pegawai,
    SPDMasukan,
    SuratTugas,
    TarifSBM,
    ValidationError,
    hitung_spd,
)


class TambahSpdDurationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.surat_tugas = {
            "id": 42,
            "status": "DRAFT",
            "tgl_berangkat": "2026-12-07",
            "tgl_kembali": "2026-12-09",
            "spd": [],
        }
        self.pegawai = {
            "id": 10,
            "nama": "Pegawai Uji",
            "nip": "123",
            "golongan": "III/a",
            "pangkat": "Penata",
            "tingkat_biaya": "C",
            "jabatan": "Analis",
            "eselon": "III.a",
        }
        self.user = {"id": 1, "role": "OPERATOR", "username": "operator"}

    def make_request(self, body):
        raw_body = json.dumps(body).encode()
        sent = False

        async def receive():
            nonlocal sent
            if sent:
                return {"type": "http.disconnect"}
            sent = True
            return {"type": "http.request", "body": raw_body, "more_body": False}

        return Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/v1/st/42/spd",
                "headers": [(b"content-type", b"application/json")],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("testclient", 123),
                "scheme": "http",
                "http_version": "1.1",
            },
            receive,
        )

    async def test_rejects_api_days_that_differ_from_surat_tugas(self):
        with (
            patch.object(main, "std", return_value=self.surat_tugas),
            patch.object(main, "q", side_effect=[self.pegawai, []]),
            patch.object(main, "hitung") as calculate,
        ):
            with self.assertRaises(HTTPException) as error:
                await main.spa(
                    42, self.make_request({"pegawai_id": 10, "hari": 30}), self.user
                )

        self.assertEqual(error.exception.detail["error"]["code"], "V1")
        calculate.assert_not_called()

    async def test_defaults_api_days_to_surat_tugas_duration(self):
        with (
            patch.object(main, "std", return_value=self.surat_tugas),
            patch.object(main, "q", side_effect=[self.pegawai, []]),
            patch.object(main, "hitung", return_value={}) as calculate,
            patch.object(main, "ex", return_value=99),
            patch.object(main, "touch"),
            patch.object(main, "log"),
        ):
            result = await main.spa(
                42, self.make_request({"pegawai_id": 10}), self.user
            )

        self.assertEqual(result["hari"], 3)
        self.assertEqual(result["malam"], 2)
        self.assertEqual(calculate.call_args.args[2], 3)
        self.assertEqual(calculate.call_args.args[3], 2)

    async def test_rejects_api_nights_that_differ_from_automatic_value(self):
        with (
            patch.object(main, "std", return_value=self.surat_tugas),
            patch.object(main, "q", side_effect=[self.pegawai, []]),
            patch.object(main, "hitung") as calculate,
        ):
            with self.assertRaises(HTTPException) as error:
                await main.spa(
                    42,
                    self.make_request({"pegawai_id": 10, "malam": 1}),
                    self.user,
                )

        self.assertEqual(error.exception.status_code, 422)
        self.assertEqual(error.exception.detail["error"]["code"], "V1")
        calculate.assert_not_called()

    async def test_same_day_trip_defaults_to_zero_nights(self):
        same_day_trip = {
            **self.surat_tugas,
            "tgl_kembali": self.surat_tugas["tgl_berangkat"],
        }
        with (
            patch.object(main, "std", return_value=same_day_trip),
            patch.object(main, "q", side_effect=[self.pegawai, []]),
            patch.object(main, "hitung", return_value={}) as calculate,
            patch.object(main, "ex", return_value=99),
            patch.object(main, "touch"),
            patch.object(main, "log"),
        ):
            result = await main.spa(
                42, self.make_request({"pegawai_id": 10}), self.user
            )

        self.assertEqual(result["hari"], 1)
        self.assertEqual(result["malam"], 0)
        self.assertEqual(calculate.call_args.args[3], 0)

    async def test_rejects_non_integer_pegawai_id_before_database_query(self):
        for invalid_id in ([10], {"id": 10}, True, 1.5, "not-an-id"):
            with self.subTest(pegawai_id=invalid_id):
                with (
                    patch.object(main, "std", return_value=self.surat_tugas),
                    patch.object(main, "q") as query,
                ):
                    with self.assertRaises(HTTPException) as error:
                        await main.spa(
                            42,
                            self.make_request({"pegawai_id": invalid_id}),
                            self.user,
                        )

                self.assertEqual(error.exception.status_code, 422)
                self.assertEqual(error.exception.detail["error"]["code"], "422")
                query.assert_not_called()

    async def test_accepts_numeric_string_pegawai_id(self):
        with (
            patch.object(main, "std", return_value=self.surat_tugas),
            patch.object(main, "q", side_effect=[self.pegawai, []]) as query,
            patch.object(main, "hitung", return_value={}),
            patch.object(main, "ex", return_value=99),
            patch.object(main, "touch"),
            patch.object(main, "log"),
        ):
            await main.spa(
                42, self.make_request({"pegawai_id": "10"}), self.user
            )

        self.assertEqual(query.call_args_list[0].args[1], (10,))


class HitungSpdDurationTests(unittest.TestCase):
    def setUp(self):
        self.surat_tugas = SuratTugas(
            nomor_surat_tugas="ST/2026/1",
            tanggal_surat_tugas=date(2026, 12, 7),
            maksud_perjalanan="Uji",
            asal="Jakarta",
            tujuan="Bandung",
            provinsi_tarif="Jawa Barat",
            tgl_berangkat=date(2026, 12, 7),
            tgl_kembali=date(2026, 12, 9),
            tgl_tanda_tangan=date(2026, 12, 7),
            akun_anggaran="",
        )
        self.pegawai = Pegawai(
            id="1",
            nama="Pegawai Uji",
            nip_nrp="123",
            golongan="III/a",
            pangkat="Penata",
            jabatan="Analis",
            eselon="III.a",
        )

    def test_rejects_days_that_exceed_surat_tugas_duration(self):
        with self.assertRaisesRegex(ValidationError, "harus sama dengan durasi Surat Tugas"):
            hitung_spd(
                self.surat_tugas,
                SPDMasukan(self.pegawai, hari=30),
                {},
                {},
                2026,
            )

    def test_rejects_days_shorter_than_surat_tugas_duration(self):
        with self.assertRaisesRegex(ValidationError, "harus sama dengan durasi Surat Tugas"):
            hitung_spd(
                self.surat_tugas,
                SPDMasukan(self.pegawai, hari=2),
                {},
                {},
                2026,
            )

    def test_caps_lodging_payment_at_sbm_and_keeps_actual_bill_rate(self):
        tarif = TarifSBM(
            tahun=2026,
            provinsi="Jawa Barat",
            uang_harian_luar_kota=100,
            uang_harian_dalam_kota_8jam=0,
            uang_harian_diklat=0,
            inap_pejabat_negara_eselon1=2755,
            inap_eselon2=2000,
            inap_eselon3_gol4=1366,
            inap_eselon4_gol321=1000,
            taksi=10,
        )

        result = hitung_spd(
            self.surat_tugas,
            SPDMasukan(self.pegawai, hari=3, malam_inap=2, tarif_inap=9000),
            {(2026, "JAWA BARAT"): tarif},
            {},
            2026,
        )

        self.assertEqual(result.tarif_inap, 9000)
        self.assertEqual(result.batas_sbm_inap, 1366)
        self.assertEqual(result.uang_penginapan, 2732)
        self.assertEqual(result.jumlah, 3042)
        self.assertTrue(result.flag_lebih_sbm)


if __name__ == "__main__":
    unittest.main()
