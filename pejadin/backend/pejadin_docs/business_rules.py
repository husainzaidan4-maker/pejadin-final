"""
Mesin perhitungan biaya perjalanan dinas + validasi.
Mengimplementasikan ATURAN PERHITUNGAN (P1-P11) dan VALIDASI (V1-V9)
dari SPEC_WEBAPP (bagian 4 & 5).

Prinsip desain (sesuai catatan spec):
  - Perhitungan ini WAJIB berjalan di backend, bukan di frontend.
  - Tidak pernah diam-diam menghasilkan 0 ketika data referensi hilang
    (P2, V2, V3) -> selalu lempar ValidationError yang jelas.
  - Tarif yang sudah dipakai untuk menerbitkan dokumen disimpan sebagai
    snapshot (lihat SPDHasil.tarif_uang_harian dkk) agar revisi PMK di
    masa depan tidak mengubah dokumen yang sudah terbit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


class ValidationError(Exception):
    """Dilempar ketika input melanggar salah satu aturan V1-V9."""


# ---------------------------------------------------------------------------
# 3.x  Model data (padanan tabel database di bagian 3 SPEC_WEBAPP)
# ---------------------------------------------------------------------------

@dataclass
class Pegawai:
    id: str
    nama: str
    nip_nrp: str
    golongan: str
    pangkat: str
    jabatan: str
    eselon: Optional[str]          # 'I.a', 'II.a', 'III.a', 'IV.a', atau None
    tingkat_biaya: Optional[str] = None
    aktif: bool = True


@dataclass
class TarifSBM:
    tahun: int
    provinsi: str
    uang_harian_luar_kota: int
    uang_harian_dalam_kota_8jam: int
    uang_harian_diklat: int
    inap_pejabat_negara_eselon1: int
    inap_eselon2: int
    inap_eselon3_gol4: int
    inap_eselon4_gol321: int
    taksi: int


@dataclass
class UangRepresentasiRate:
    tahun: int
    kategori: str          # PEJABAT_NEGARA | ESELON_I | ESELON_II
    luar_kota_oh: int
    dalam_kota_8jam: int


@dataclass
class SuratTugas:
    nomor_surat_tugas: str
    tanggal_surat_tugas: Optional[date]
    maksud_perjalanan: str
    asal: str
    tujuan: str
    provinsi_tarif: str
    tgl_berangkat: date
    tgl_kembali: date
    tgl_tanda_tangan: Optional[date]
    akun_anggaran: str
    nama_kegiatan: Optional[str] = None
    alat_angkutan: Optional[str] = None
    jenis_kuitansi: Optional[str] = None       # UP | LS
    status: str = "DRAFT"                      # DRAFT | TERBIT | SELESAI | DIBATALKAN
    uraian_kegiatan: Optional[str] = None       # untuk dokumen LAPORAN
    keterangan_laporan: Optional[str] = None    # untuk dokumen LAPORAN


@dataclass
class SPDMasukan:
    """Data yang DIINPUT (bukan hasil hitung) untuk satu pelaksana pada satu Surat Tugas."""
    pegawai: Pegawai
    hari: int                       # harus sama dengan durasi Surat Tugas
    malam_inap: int = 0
    tarif_inap: Optional[int] = None   # Tarif aktual dari tagihan hotel per malam
    transport_tiket: int = 0           # AT-COST, manual
    biaya_lain: int = 0


@dataclass
class SPDHasil:
    """Hasil perhitungan untuk satu pelaksana (kolom 'turunan' di tabel spd)."""
    pegawai: Pegawai
    hari: int
    tarif_uang_harian: int
    uang_harian: int
    malam_inap: int
    tarif_inap: int                  # tarif tagihan aktual per malam
    uang_penginapan: int
    transport_tiket: int
    taksi: int
    biaya_lain: int
    tarif_representasi: int
    uang_representasi: int
    jumlah: int
    batas_sbm_inap: int
    flag_lebih_sbm: bool
    ppn: Optional[int] = None
    pph: Optional[int] = None


# ---------------------------------------------------------------------------
# P1 - Lama perjalanan
# ---------------------------------------------------------------------------

def hitung_lama_hari(tgl_berangkat: date, tgl_kembali: date) -> int:
    """P1: lama = tgl_kembali - tgl_berangkat + 1 (inklusif). Tolak bila negatif/nol."""
    lama = (tgl_kembali - tgl_berangkat).days + 1
    if lama < 1:
        # V1
        raise ValidationError(
            f"V1: tanggal kembali ({tgl_kembali}) harus >= tanggal berangkat ({tgl_berangkat})."
        )
    return lama


# ---------------------------------------------------------------------------
# Lookup tarif (dengan larangan diam-diam pakai 0)
# ---------------------------------------------------------------------------

def cari_tarif_sbm(tabel: dict[tuple[int, str], TarifSBM], tahun: int, provinsi: str) -> TarifSBM:
    """
    V2 + V3 + P2: provinsi wajib ada di daftar 38 provinsi tahun berjalan.
    Bila tidak ketemu -> ValidationError (BUKAN return 0, beda dari Excel lama
    yang memakai IFERROR -> 0).
    """
    key = (tahun, provinsi.strip().upper())
    tarif = tabel.get(key)
    if tarif is None:
        raise ValidationError(
            f"V2/V3: tarif SBM untuk provinsi '{provinsi}' tahun {tahun} tidak ditemukan. "
            f"Pastikan provinsi dipilih dari dropdown 38 provinsi dan PMK tahun {tahun} sudah diunggah."
        )
    return tarif


def _kategori_eselon(eselon: Optional[str]) -> Optional[str]:
    """Peta string eselon (mis. 'I.a', 'II.b') ke kategori kasar I/II/III/IV."""
    if not eselon:
        return None
    e = eselon.strip().upper()
    if e.startswith("I."):
        return "I"
    if e.startswith("II."):
        return "II"
    if e.startswith("III."):
        return "III"
    if e.startswith("IV."):
        return "IV"
    return None


# ---------------------------------------------------------------------------
# P5 - Tarif & uang representasi
# ---------------------------------------------------------------------------

def hitung_tarif_representasi(pegawai: Pegawai, rep_rates: dict[tuple[int, str], UangRepresentasiRate], tahun: int) -> int:
    """
    P5: Eselon I -> 200.000/hari; Eselon II -> 150.000/hari; Eselon III & IV -> 0.
    Kategori 'Pejabat Negara/Wakil Menteri' (250.000) TERSEDIA di tabel tapi
    belum diaktifkan (Q2 di spec belum dikonfirmasi pengguna) -> diperlakukan
    sama dengan Eselon I bila muncul, sesuai perilaku Excel saat ini.
    """
    kategori = _kategori_eselon(pegawai.eselon)
    if kategori == "I":
        rate = rep_rates.get((tahun, "ESELON_I"))
        return rate.luar_kota_oh if rate else 200_000
    if kategori == "II":
        rate = rep_rates.get((tahun, "ESELON_II"))
        return rate.luar_kota_oh if rate else 150_000
    return 0


# ---------------------------------------------------------------------------
# P4 - Taksi
# ---------------------------------------------------------------------------

def hitung_taksi(tarif_representasi: int, tarif_sbm: TarifSBM) -> int:
    """P4: taksi = 0 bila berhak representasi (Eselon I & II); selain itu = tarif taksi provinsi."""
    if tarif_representasi > 0:
        return 0
    return tarif_sbm.taksi


# ---------------------------------------------------------------------------
# Batas SBM inap (batas pembayaran, V9) - P3 catatan
# ---------------------------------------------------------------------------

def hitung_batas_sbm_inap(pegawai: Pegawai, tarif_sbm: TarifSBM) -> int:
    """
    Batas atas penginapan per malam menurut eselon/golongan.
    Urutan sesuai spec baris 140:
      Pejabat Negara/Eselon I -> inap_pejabat_negara_eselon1
      Eselon II               -> inap_eselon2
      Eselon III atau Gol IV  -> inap_eselon3_gol4
      Eselon IV atau Gol I/II/III -> inap_eselon4_gol321
    """
    kategori = _kategori_eselon(pegawai.eselon)
    golongan_utama = (pegawai.golongan or "").split("/")[0].strip().upper()

    if kategori == "I":
        return tarif_sbm.inap_pejabat_negara_eselon1
    if kategori == "II":
        return tarif_sbm.inap_eselon2
    if kategori == "III" or golongan_utama == "IV":
        return tarif_sbm.inap_eselon3_gol4
    # Eselon IV atau golongan III/II/I (termasuk pegawai tanpa eselon)
    return tarif_sbm.inap_eselon4_gol321


# ---------------------------------------------------------------------------
# Perhitungan penuh 1 pelaksana (P1-P6, V1-V9)
# ---------------------------------------------------------------------------

def hitung_spd(
    surat_tugas: SuratTugas,
    masukan: SPDMasukan,
    tarif_sbm_table: dict[tuple[int, str], TarifSBM],
    rep_rates: dict[tuple[int, str], UangRepresentasiRate],
    tahun: int,
) -> SPDHasil:
    pegawai = masukan.pegawai

    # V7: eselon & golongan wajib terisi
    if not (pegawai.eselon and pegawai.eselon.strip()) or not (pegawai.golongan and pegawai.golongan.strip()):
        raise ValidationError(f"V7: Eselon & golongan '{pegawai.nama}' belum terisi.")

    # P1 / V1: hari pelaksana harus mengikuti durasi Surat Tugas.
    if masukan.hari < 1:
        raise ValidationError(f"V1: jumlah hari pelaksana '{pegawai.nama}' harus >= 1.")
    lama_hari = hitung_lama_hari(surat_tugas.tgl_berangkat, surat_tugas.tgl_kembali)
    if masukan.hari != lama_hari:
        raise ValidationError(
            f"V1: jumlah hari pelaksana '{pegawai.nama}' harus sama dengan "
            f"durasi Surat Tugas ({lama_hari} hari)."
        )
    if masukan.malam_inap < 0 or masukan.transport_tiket < 0 or masukan.biaya_lain < 0:
        raise ValidationError("V4: malam inap dan biaya tidak boleh negatif.")
    if masukan.tarif_inap is not None and masukan.tarif_inap < 0:
        raise ValidationError("V4: tarif_inap tidak boleh negatif.")

    tarif_sbm = cari_tarif_sbm(tarif_sbm_table, tahun, surat_tugas.provinsi_tarif)  # P2 / V2 / V3

    # P2: uang harian
    tarif_harian = tarif_sbm.uang_harian_luar_kota
    uang_harian = masukan.hari * tarif_harian

    # P5: representasi
    tarif_representasi = hitung_tarif_representasi(pegawai, rep_rates, tahun)
    uang_representasi = masukan.hari * tarif_representasi

    # P4: taksi
    taksi = hitung_taksi(tarif_representasi, tarif_sbm)

    # V4: malam_inap <= hari - 1
    if masukan.malam_inap > masukan.hari - 1:
        raise ValidationError(
            f"V4: malam inap ({masukan.malam_inap}) untuk '{pegawai.nama}' melebihi "
            f"hari perjalanan dikurangi 1 ({masukan.hari - 1})."
        )
    if masukan.malam_inap > 0 and not masukan.tarif_inap:
        # V4 lanjutan: cegah uang penginapan diam-diam jadi 0
        raise ValidationError(
            f"V4: malam inap > 0 untuk '{pegawai.nama}' tetapi tarif_inap (bill hotel) belum diisi."
        )

    # P3: simpan tarif tagihan aktual, tetapi batasi nilai yang dibayar sesuai SBM.
    tarif_inap = masukan.tarif_inap or 0
    batas_sbm_inap = hitung_batas_sbm_inap(pegawai, tarif_sbm)
    flag_lebih_sbm = tarif_inap > batas_sbm_inap
    tarif_inap_dibayar = min(tarif_inap, batas_sbm_inap)
    uang_penginapan = masukan.malam_inap * tarif_inap_dibayar

    # P6: jumlah total
    jumlah = (
        uang_harian
        + uang_penginapan
        + masukan.transport_tiket
        + taksi
        + masukan.biaya_lain
        + uang_representasi
    )

    return SPDHasil(
        pegawai=pegawai,
        hari=masukan.hari,
        tarif_uang_harian=tarif_harian,
        uang_harian=uang_harian,
        malam_inap=masukan.malam_inap,
        tarif_inap=tarif_inap,
        uang_penginapan=uang_penginapan,
        transport_tiket=masukan.transport_tiket,
        taksi=taksi,
        biaya_lain=masukan.biaya_lain,
        tarif_representasi=tarif_representasi,
        uang_representasi=uang_representasi,
        jumlah=jumlah,
        batas_sbm_inap=batas_sbm_inap,
        flag_lebih_sbm=flag_lebih_sbm,
    )


def hitung_surat_tugas(
    surat_tugas: SuratTugas,
    daftar_masukan: list[SPDMasukan],
    tarif_sbm_table: dict[tuple[int, str], TarifSBM],
    rep_rates: dict[tuple[int, str], UangRepresentasiRate],
    tahun: int,
) -> tuple[int, list[SPDHasil]]:
    """P1 (lama_hari), lalu hitung tiap pelaksana. Return (total_biaya, hasil per pelaksana)."""
    lama_hari = hitung_lama_hari(surat_tugas.tgl_berangkat, surat_tugas.tgl_kembali)  # P1 / V1

    hasil_list = [
        hitung_spd(surat_tugas, masukan, tarif_sbm_table, rep_rates, tahun)
        for masukan in daftar_masukan
    ]
    total_biaya = sum(h.jumlah for h in hasil_list)  # jml_orang = len(hasil_list)
    return total_biaya, hasil_list


# V5: SPD pegawai tidak boleh tumpang tindih tanggal (dicek di level "database"/layanan,
# butuh riwayat semua SPD pegawai, jadi disediakan sebagai fungsi util terpisah di sini)

def cek_tumpang_tindih(
    pegawai_id: str,
    tgl_berangkat: date,
    tgl_kembali: date,
    riwayat_spd: list[tuple[str, date, date]],
) -> bool:
    """
    V5: True bila ada SPD lain milik pegawai yang sama dengan rentang tanggal bertumpang tindih.
    riwayat_spd: list of (pegawai_id, tgl_berangkat, tgl_kembali) SPD lain yang sudah TERBIT/SELESAI.
    """
    for pid, mulai, selesai in riwayat_spd:
        if pid != pegawai_id:
            continue
        if tgl_berangkat <= selesai and mulai <= tgl_kembali:
            return True
    return False


# V6: nomor surat tugas unik per tahun

def cek_nomor_unik(nomor_surat_tugas: str, nomor_yang_sudah_ada: set[str]) -> None:
    if nomor_surat_tugas in nomor_yang_sudah_ada:
        raise ValidationError(f"V6: nomor Surat Tugas '{nomor_surat_tugas}' sudah dipakai.")


# V8: dokumen hanya bisa dicetak bila status TERBIT/SELESAI

def cek_boleh_cetak(surat_tugas: SuratTugas) -> None:
    if surat_tugas.status not in ("TERBIT", "SELESAI"):
        raise ValidationError(
            f"V8: Surat Tugas berstatus '{surat_tugas.status}' belum bisa dicetak "
            f"(harus TERBIT atau SELESAI)."
        )
