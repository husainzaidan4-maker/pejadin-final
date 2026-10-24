"""Generator PDF: Laporan Pelaksanaan Perjalanan Dinas. Padanan sheet 'LAPORAN'. TTD: pelaksana."""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from .pdf_common import W, H, MARGIN, fmt_tgl_tulis_tangan, fmt_periode, paragraf


def buat_pdf_laporan(path: str, satker: dict, surat_tugas, daftar_pelaksana: list):
    """daftar_pelaksana: list of business_rules.Pegawai."""
    c = canvas.Canvas(path, pagesize=A4)
    x0 = MARGIN
    y = H - MARGIN
    isi_w = W - MARGIN - (x0 + 55 * mm)

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(W / 2, y, "LAPORAN PELAKSANAAN PERJALANAN DINAS")
    y -= 10 * mm

    c.setFont("Helvetica", 9.5)
    x_label = x0
    x_isi = x0 + 55 * mm

    def baris(label, isi):
        nonlocal y
        c.drawString(x_label, y, label)
        c.drawString(x_label + 48 * mm, y, ":")
        c.drawString(x_isi, y, isi)
        y -= 5 * mm

    baris("Nomor Surat Tugas", surat_tugas.nomor_surat_tugas)
    baris("Periode Perjalanan Dinas", fmt_periode(surat_tugas.tgl_berangkat, surat_tugas.tgl_kembali))
    baris("Kota Tujuan Perjalanan Dinas", surat_tugas.tujuan)

    c.drawString(x_label, y, "Nama Pelaksana Perjalanan Dinas")
    c.drawString(x_label + 48 * mm, y, ":")
    for i, peg in enumerate(daftar_pelaksana, start=1):
        c.drawString(x_isi, y, f"{i}. {peg.nama} / NIP. {peg.nip_nrp}")
        y -= 4.5 * mm
    y -= 4 * mm

    y = paragraf(c, f"Berdasarkan Surat Tugas Nomor {surat_tugas.nomor_surat_tugas} tanggal "
                    f"{fmt_tgl_tulis_tangan(surat_tugas.tanggal_surat_tugas)} bersama ini kami sampaikan "
                    "laporan pelaksanaan perjalanan dinas sebagai berikut:", x0, y, W - 2 * MARGIN,
                 size=9.5, leading=12.5)
    y -= 8 * mm

    # Tabel uraian kegiatan
    cols = [("NO.", 10 * mm), ("URAIAN KEGIATAN", 105 * mm), ("KETERANGAN", 55 * mm)]
    x_pos = []
    xc = x0
    for _, w in cols:
        x_pos.append(xc)
        xc += w
    table_right = xc
    y_top = y

    c.setFont("Helvetica-Bold", 9)
    for (label, w), xp in zip(cols, x_pos):
        c.drawString(xp + 1 * mm, y - 4.5 * mm, label)
    y -= 7 * mm
    c.line(x0, y, table_right, y)

    uraian = surat_tugas.uraian_kegiatan or surat_tugas.maksud_perjalanan
    keterangan = surat_tugas.keterangan_laporan or "-"

    c.setFont("Helvetica", 9)
    y_u = paragraf(c, uraian, x_pos[1] + 1 * mm, y - 3 * mm, cols[1][1] - 2 * mm, size=9, leading=11.5)
    y_k = paragraf(c, keterangan, x_pos[2] + 1 * mm, y - 3 * mm, cols[2][1] - 2 * mm, size=9, leading=11.5)
    c.drawString(x_pos[0] + 1 * mm, y - 3 * mm, "1")
    y_bawah = min(y_u, y_k) - 3 * mm

    for xp in x_pos[1:]:
        c.line(xp, y, xp, y)  # placeholder no-op (garis kolom sudah cukup di header)
    c.rect(x0, y_bawah, table_right - x0, y - y_bawah)
    for xp in x_pos[1:]:
        c.line(xp, y_bawah, xp, y)
    y = y_bawah - 10 * mm

    xkanan = W - MARGIN - 65 * mm
    c.setFont("Helvetica", 9)
    c.drawString(xkanan, y, f"{satker['kota_kedudukan']}, {fmt_tgl_tulis_tangan(surat_tugas.tgl_tanda_tangan)}")
    y -= 5 * mm
    c.drawString(xkanan, y, "Pelaksana SPD")
    y -= 20 * mm
    for i, peg in enumerate(daftar_pelaksana):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(xkanan, y, peg.nama)
        y -= 4.5 * mm
        c.setFont("Helvetica", 9)
        c.drawString(xkanan, y, f"NIP. {peg.nip_nrp}")
        y -= 8 * mm

    c.showPage()
    c.save()
