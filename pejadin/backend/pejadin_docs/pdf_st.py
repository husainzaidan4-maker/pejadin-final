"""
Generator PDF: Surat Tugas (ST) + Lampiran Surat Tugas (daftar pelaksana).
Padanan sheet 'ST' dan 'ST_LAMPIRAN'. TTD: SEKDITJEN (ST ditandatangani atas
nama SEKDITJEN; PPK & Kabag hanya paraf).
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from .pdf_common import (
    W, H, MARGIN, fmt_tgl_tulis_tangan, fmt_periode, paragraf,
    blok_paraf_tiga,
)


def buat_pdf_st(path: str, satker: dict, pejabat: dict, dasar_hukum: list, surat_tugas):
    """
    pejabat: dict {peran: {'nama':.., 'nip':.., 'jabatan_lengkap':..}} (dari REF bagian B)
    dasar_hukum: list of {'urutan':.., 'teks':..} (dari REF bagian C)
    """
    c = canvas.Canvas(path, pagesize=A4)
    x0 = MARGIN
    isi_w = W - 2 * MARGIN - 8 * mm
    y = H - MARGIN

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W / 2, y, "SURAT TUGAS")
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    c.drawCentredString(W / 2, y, f"NOMOR : {surat_tugas.nomor_surat_tugas}")
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W / 2, y, pejabat["SEKDITJEN"]["jabatan_lengkap"].upper())
    y -= 10 * mm

    kegiatan_txt = f", pada Kegiatan {surat_tugas.nama_kegiatan}," if surat_tugas.nama_kegiatan else ","

    x_label = x0
    x_kolon = x0 + 22 * mm
    x_huruf = x_kolon + 5 * mm
    x_isi = x_huruf + 6 * mm
    isi_w2 = W - MARGIN - x_isi

    def item(huruf, teks):
        nonlocal y
        c.setFont("Helvetica", 9.5)
        label_text = str(huruf) if str(huruf).endswith(".") else f"{huruf}."
        c.drawString(x_huruf, y - 3.2 * mm, label_text)
        y_baru = paragraf(c, teks, x_isi, y, isi_w2, size=9.5, leading=12.5)
        y = y_baru - 2 * mm

    c.setFont("Helvetica", 9.5)
    c.drawString(x_label, y, "Menimbang")
    c.drawString(x_kolon, y, ":")
    item("a", f"bahwa dalam rangka {surat_tugas.maksud_perjalanan} ke {surat_tugas.tujuan}"
              f"{kegiatan_txt} yang akan melakukan perjalanan dinas sesuai jadwal terlampir "
              f"dengan ketentuan;")
    item("b", "bahwa para pejabat/pegawai di lingkungan Setditjen SDA Kementerian PU yang "
              "namanya disebut dalam surat tugas ini memenuhi kriteria untuk melaksanakan "
              "tugas yang dimaksud;")
    item("c", "bahwa untuk keperluan tersebut pada huruf a dan b perlu menetapkan surat tugas.")

    y -= 1 * mm
    c.drawString(x_label, y, "Dasar")
    c.drawString(x_kolon, y, ":")
    for d in dasar_hukum:
        item(d["urutan"], d["teks"])

    y -= 3 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W / 2, y, "MEMBERI TUGAS")
    y -= 8 * mm

    c.setFont("Helvetica", 9.5)
    c.drawString(x_label, y, "Kepada")
    c.drawString(x_kolon, y, ":")
    y = paragraf(c, "(Daftar Pejabat dan Pegawai Terlampir)", x_isi, y, isi_w2, size=9.5)
    y -= 4 * mm

    c.drawString(x_label, y, "Untuk")
    c.drawString(x_kolon, y, ":")
    item(1, f"Melaksanakan tugas dalam rangka {surat_tugas.maksud_perjalanan} di "
            f"{surat_tugas.tujuan}{kegiatan_txt} yang akan melakukan perjalanan dinas sesuai "
            f"jadwal terlampir dengan ketentuan;")
    item(2, "Kepada pegawai tersebut di atas agar melaksanakan perjalanan dinas sesuai dengan "
            "rincian Surat Tugas dan menyampaikan laporan pelaksanaan perjalanan dinas kepada "
            f"{pejabat['SEKDITJEN']['jabatan_lengkap']} selambat-lambatnya 5 (lima) hari kerja "
            "setelah pelaksanaan perjalanan dinas;")
    item(3, "Melaporkan diri kepada Pimpinan setiba di tujuan untuk mendapatkan arahan;")
    item(4, "Melaksanakan Surat Perintah ini dengan penuh tanggung jawab dan setelah selesai "
            "agar membuat laporan secara tertulis;")
    item(5, "Apabila dikemudian hari terdapat kekeliruan dalam surat tugas ini, akan diadakan "
            "perbaikan sebagaimana mestinya.")

    y -= 4 * mm
    c.setFont("Helvetica", 9.5)
    c.drawRightString(W - MARGIN, y, f"{satker['kota_kedudukan']}, {fmt_tgl_tulis_tangan(surat_tugas.tgl_tanda_tangan)}")
    y -= 10 * mm

    y = blok_paraf_tiga(c, y, pejabat["PPK"], pejabat["KABAG"], pejabat["SEKDITJEN"])

    y -= 10 * mm
    c.setFont("Helvetica", 9)
    c.drawString(x0, y, "Tembusan:")
    y -= 4.5 * mm
    c.drawString(x0, y, "Pejabat Pembuat Komitmen Setditjen SDA")

    c.showPage()
    c.save()


def buat_pdf_st_lampiran(path: str, satker: dict, pejabat: dict, surat_tugas, daftar_pelaksana: list):
    """
    daftar_pelaksana: list of business_rules.Pegawai (semua pelaksana pada Surat Tugas ini)
    """
    c = canvas.Canvas(path, pagesize=A4)
    x0 = MARGIN
    y = H - MARGIN

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W / 2, y, "DAFTAR LAMPIRAN SURAT TUGAS")
    y -= 6 * mm
    c.setFont("Helvetica", 9.5)
    c.drawCentredString(W / 2, y, f"NOMOR      : {surat_tugas.nomor_surat_tugas}")
    y -= 4.5 * mm
    c.drawCentredString(W / 2, y, f"TANGGAL : {fmt_tgl_tulis_tangan(surat_tugas.tanggal_surat_tugas)}")
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x0, y, "DAFTAR NAMA PEGAWAI")
    y -= 6 * mm

    # Tabel
    cols = [
        ("NO.", 8 * mm),
        ("PELAKSANA SPD", 45 * mm),
        ("UNIT KERJA", 33 * mm),
        ("PERIODE PERJALANAN", 30 * mm),
        ("TUJUAN", 20 * mm),
        ("PEMBEBANAN ANGGARAN", 34 * mm),
    ]
    x_positions = []
    xc = x0
    for label, w in cols:
        x_positions.append(xc)
        xc += w
    table_right = xc

    row_h = 6 * mm
    header_h = 8 * mm
    y_header_top = y

    def garis_tabel(y_bawah_header):
        c.rect(x0, y_bawah_header, table_right - x0, y_header_top - y_bawah_header)
        for xp in x_positions[1:]:
            c.line(xp, y_bawah_header, xp, y_header_top)
        c.line(x0, y_header_top - header_h, table_right, y_header_top - header_h)

    c.setFont("Helvetica-Bold", 8)
    yh = y_header_top - 5.5 * mm
    for (label, w), xp in zip(cols, x_positions):
        paragraf(c, label, xp + 1 * mm, y_header_top - 1 * mm, w - 2 * mm, font="Helvetica-Bold", size=7.5, leading=9)
    y = y_header_top - header_h

    c.setFont("Helvetica", 8)
    periode = fmt_periode(surat_tugas.tgl_berangkat, surat_tugas.tgl_kembali)

    for i, peg in enumerate(daftar_pelaksana, start=1):
        baris_top = y
        pelaksana_txt = f"{peg.nama}<br/>NIP {peg.nip_nrp}<br/>GOL {peg.golongan}<br/>{peg.jabatan}"

        y_no = paragraf(c, str(i), x_positions[0] + 1 * mm, baris_top - 3 * mm,
                         cols[0][1] - 2 * mm, size=8, leading=10)
        y_pelaksana = paragraf(c, pelaksana_txt, x_positions[1] + 1 * mm, baris_top - 3 * mm,
                                cols[1][1] - 2 * mm, size=8, leading=10)
        y_unit = paragraf(c, satker["nama_satker"], x_positions[2] + 1 * mm, baris_top - 3 * mm,
                           cols[2][1] - 2 * mm, size=8, leading=10)
        y_periode = paragraf(c, periode, x_positions[3] + 1 * mm, baris_top - 3 * mm,
                              cols[3][1] - 2 * mm, size=8, leading=10)
        y_tujuan = paragraf(c, surat_tugas.tujuan, x_positions[4] + 1 * mm, baris_top - 3 * mm,
                             cols[4][1] - 2 * mm, size=8, leading=10)
        y_akun = paragraf(c, surat_tugas.akun_anggaran, x_positions[5] + 1 * mm, baris_top - 3 * mm,
                           cols[5][1] - 2 * mm, size=8, leading=10)

        y = min(y_no, y_pelaksana, y_unit, y_periode, y_tujuan, y_akun) - 3 * mm

    # garis luar & kolom
    c.rect(x0, y, table_right - x0, y_header_top - y)
    for xp in x_positions[1:]:
        c.line(xp, y, xp, y_header_top)
    c.line(x0, y_header_top - header_h, table_right, y_header_top - header_h)

    y -= 15 * mm
    y = blok_paraf_tiga(c, y, pejabat["PPK"], pejabat["KABAG"], pejabat["SEKDITJEN"])

    c.showPage()
    c.save()
