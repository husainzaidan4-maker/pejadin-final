"""Generator PDF: Surat Pernyataan Tanggung Jawab Belanja. Padanan sheet 'SPTJB'. TTD: PPK."""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from .pdf_common import W, H, MARGIN, fmt_tgl_tulis_tangan, rp, paragraf
from .terbilang import rupiah_terbilang


def buat_pdf_sptjb(path: str, satker: dict, pejabat_ppk: dict, surat_tugas, hasil_list: list):
    """
    hasil_list: list of business_rules.SPDHasil (semua pelaksana pada Surat Tugas ini).
    Satu baris tabel per pelaksana.
    """
    c = canvas.Canvas(path, pagesize=A4)
    x0 = MARGIN
    y = H - MARGIN

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(W / 2, y, "SURAT PERNYATAAN TANGGUNG JAWAB BELANJA")
    y -= 6 * mm
    c.setFont("Helvetica", 9.5)
    c.drawCentredString(W / 2, y, f"Nomor : {satker['nomor_sptjb']}")
    y -= 10 * mm

    c.setFont("Helvetica", 9.5)
    for no, label, isi in [
        (1, "Kode Satuan Kerja", str(satker["kode_satker"])),
        (2, "Nama Satuan Kerja", satker["nama_satker"]),
        (3, "Tanggal / Nomor DIPA", satker["dipa_raw"]),
        (4, "Klasifikasi Anggaran", satker["klasifikasi_anggaran"]),
    ]:
        c.drawString(x0, y, f"{no}.")
        c.drawString(x0 + 8 * mm, y, label)
        c.drawString(x0 + 55 * mm, y, f": {isi}")
        y -= 5 * mm
    y -= 3 * mm

    y = paragraf(c, "Yang bertanda tangan di bawah ini atas nama Kuasa Pengguna Anggaran "
                    f"{satker['nama_satker']} menyatakan bahwa saya bertanggung jawab secara "
                    "formal dan material dan kebenaran perhitungan pemungutan pajak atas segala "
                    "pembayaran tagihan yang telah kami perintahkan dalam SPM ini dengan "
                    "perincian sebagai berikut :", x0, y, W - 2 * MARGIN, size=9.5, leading=12.5)
    y -= 6 * mm

    # Tabel
    cols = [("NO", 7 * mm), ("AKUN", 25 * mm), ("PENERIMA", 32 * mm),
            ("URAIAN", 58 * mm), ("JUMLAH", 26 * mm), ("PPN", 11 * mm), ("PPh", 11 * mm)]
    x_pos = []
    xc = x0
    for _, w in cols:
        x_pos.append(xc)
        xc += w
    table_right = xc
    y_top = y

    c.setFont("Helvetica-Bold", 8)
    for (label, w), xp in zip(cols, x_pos):
        c.drawString(xp + 1 * mm, y - 4 * mm, label)
    y -= 7 * mm
    c.line(x0, y, table_right, y)

    c.setFont("Helvetica", 7.5)
    total = 0
    for i, h in enumerate(hasil_list, start=1):
        uraian = f"Belanja Perjalanan Dinas untuk {surat_tugas.maksud_perjalanan} ke " \
                 f"{surat_tugas.tujuan} a.n {h.pegawai.nama}"
        row_top = y
        p_y = paragraf(c, uraian, x_pos[3] + 1 * mm, y - 3 * mm, cols[3][1] - 2 * mm, size=7.5, leading=9.5)
        tinggi = max(6 * mm, row_top - p_y + 3 * mm)
        yy = row_top - 4 * mm
        c.drawString(x_pos[0] + 1 * mm, yy, str(i))
        c.drawString(x_pos[1] + 1 * mm, yy, surat_tugas.akun_anggaran)
        c.drawString(x_pos[2] + 1 * mm, yy, f"{i}. {h.pegawai.nama}")
        c.drawRightString(x_pos[4] + cols[4][1] - 1 * mm, yy, rp(h.jumlah))
        c.drawRightString(x_pos[5] + cols[5][1] - 1 * mm, yy, rp(h.ppn))
        c.drawRightString(x_pos[6] + cols[6][1] - 1 * mm, yy, rp(h.pph))
        total += h.jumlah
        y = row_top - tinggi

    c.line(x0, y, table_right, y)
    y -= 4.5 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x_pos[3] + 1 * mm, y, "Jumlah")
    c.drawRightString(x_pos[4] + cols[4][1] - 1 * mm, y, rp(total))
    c.drawString(x_pos[5] + 1 * mm, y, "-")
    c.drawString(x_pos[6] + 1 * mm, y, "-")
    y -= 7 * mm

    c.setFont("Helvetica", 9)
    c.drawString(x0, y, f"Terbilang : {rupiah_terbilang(total)}")
    y -= 9 * mm

    y = paragraf(c, "Bukti-bukti pengeluaran anggaran dan asli setoran pajak (SSP / BPN) tersebut "
                    "di atas disimpan oleh Pengguna Anggaran / Kuasa Pengguna Anggaran untuk "
                    "kelengkapan administrasi dan pemeriksaan aparat pengawasan fungsional.",
                 x0, y, W - 2 * MARGIN, size=8.5, leading=11)
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(x0, y, "Demikian Surat Pernyataan ini dibuat dengan sebenarnya.")
    y -= 10 * mm

    xkanan = W - MARGIN - 65 * mm
    c.drawString(xkanan, y, f"{satker['kota_kedudukan']}, {fmt_tgl_tulis_tangan(surat_tugas.tgl_tanda_tangan)}")
    y -= 5 * mm
    c.drawString(xkanan, y, "Pejabat Pembuat Komitmen")
    y -= 4.5 * mm
    c.drawString(xkanan, y, satker["nama_satker"])
    y -= 18 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(xkanan, y, pejabat_ppk["nama"])
    y -= 4.5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(xkanan, y, f"NIP. {pejabat_ppk['nip']}")

    c.showPage()
    c.save()
