"""Generator PDF: Daftar Nominatif Penerima. Padanan sheet 'NOMINATIF'.
TTD: Pembuat Daftar + Bendahara + PPK."""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from .pdf_common import W, H, MARGIN, fmt_tgl_tulis_tangan, fmt_periode, rp, paragraf
from .terbilang import rupiah_terbilang


def buat_pdf_nominatif(path: str, satker: dict, pejabat: dict, surat_tugas, hasil_list: list):
    c = canvas.Canvas(path, pagesize=A4)
    x0 = MARGIN
    y = H - MARGIN

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W / 2, y, "REKAPITULASI DAFTAR NOMINATIF PERJALANAN DINAS DALAM RANGKA")
    y -= 5 * mm
    c.setFont("Helvetica", 9.5)
    c.drawCentredString(W / 2, y, surat_tugas.maksud_perjalanan)
    y -= 8 * mm
    c.drawString(x0, y, f"REKENING BENDAHARA PENGELUARAN : {satker['rekening_bendahara']}")
    y -= 8 * mm

    cols = [("No.", 8 * mm), ("NAMA", 26 * mm), ("NIP/NRP", 26 * mm), ("GOL", 12 * mm),
            ("ASAL", 16 * mm), ("TUJUAN", 16 * mm), ("TGL BERANGKAT-KEMBALI", 32 * mm),
            ("LAMA", 12 * mm), ("BIAYA (Rp)", 20 * mm)]
    x_pos = []
    xc = x0
    for _, w in cols:
        x_pos.append(xc)
        xc += w
    table_right = xc
    y_top = y

    c.setFont("Helvetica-Bold", 7.5)
    for (label, w), xp in zip(cols, x_pos):
        paragraf(c, label, xp + 1 * mm, y - 1 * mm, w - 2 * mm, font="Helvetica-Bold", size=7, leading=8.5)
    y -= 9 * mm
    c.line(x0, y, table_right, y)

    c.setFont("Helvetica", 7.5)
    total = 0
    periode = fmt_periode(surat_tugas.tgl_berangkat, surat_tugas.tgl_kembali)
    for i, h in enumerate(hasil_list, start=1):
        row_top = y
        y_nama = paragraf(c, h.pegawai.nama, x_pos[1] + 1 * mm, row_top - 3 * mm, cols[1][1] - 2 * mm, size=7.5, leading=9)
        y_nip = paragraf(c, h.pegawai.nip_nrp, x_pos[2] + 1 * mm, row_top - 3 * mm, cols[2][1] - 2 * mm, size=7.5, leading=9)
        y_periode = paragraf(c, periode, x_pos[6] + 1 * mm, row_top - 3 * mm, cols[6][1] - 2 * mm, size=7.5, leading=9)
        yy = row_top - 3 * mm
        c.drawString(x_pos[0] + 1 * mm, yy, str(i))
        c.drawString(x_pos[3] + 1 * mm, yy, h.pegawai.golongan)
        c.drawString(x_pos[4] + 1 * mm, yy, surat_tugas.asal)
        c.drawString(x_pos[5] + 1 * mm, yy, surat_tugas.tujuan)
        c.drawString(x_pos[7] + 1 * mm, yy, f"{h.hari} Hari")
        c.drawRightString(x_pos[8] + cols[8][1] - 1 * mm, yy, rp(h.jumlah))
        total += h.jumlah
        y = min(y_nama, y_nip, y_periode, row_top - 6 * mm) - 2 * mm

    c.line(x0, y, table_right, y)
    y -= 4.5 * mm
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x_pos[0] + 1 * mm, y, "JUMLAH :")
    c.drawRightString(x_pos[8] + cols[8][1] - 1 * mm, y, rp(total))
    y -= 6 * mm
    c.setFont("Helvetica", 9)
    c.drawString(x_pos[2], y, f"Terbilang : {rupiah_terbilang(total)}")
    y -= 12 * mm

    xkanan = W - MARGIN - 70 * mm
    c.drawString(xkanan, y, f"{satker['kota_kedudukan']}, {fmt_tgl_tulis_tangan(surat_tugas.tgl_tanda_tangan)}")
    y -= 5 * mm
    c.drawString(xkanan, y, "Pejabat Pembuat Komitmen")
    y -= 4.5 * mm
    c.drawString(xkanan, y, satker["nama_satker"])
    y -= 18 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(xkanan, y, pejabat["PPK"]["nama"])
    y -= 4.5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(xkanan, y, f"NIP. {pejabat['PPK']['nip']}")
    y -= 12 * mm

    # Pembuat Daftar + Bendahara (kiri & tengah)
    xkiri = x0
    xtengah = x0 + 70 * mm
    c.setFont("Helvetica", 9)
    c.drawString(xkiri, y, "Pembuat Daftar")
    c.drawString(xtengah, y, "Bendahara Pengeluaran")
    y -= 18 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(xkiri, y, pejabat["PEMBUAT_DAFTAR"]["nama"])
    c.drawString(xtengah, y, pejabat["BENDAHARA"]["nama"])
    y -= 4.5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(xkiri, y, f"NIP. {pejabat['PEMBUAT_DAFTAR']['nip']}")
    c.drawString(xtengah, y, f"NIP. {pejabat['BENDAHARA']['nip']}")

    c.showPage()
    c.save()
