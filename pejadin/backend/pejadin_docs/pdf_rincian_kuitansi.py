"""
Generator PDF: Rincian Biaya Perjalanan Dinas + Kuitansi.
Padanan sheet 'RINCIAN' dan 'KUITANSI'.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

from .pdf_common import fmt_tgl_tulis_tangan
from .terbilang import rupiah_terbilang

W, H = A4
MARGIN = 20 * mm


def _rp(n: int) -> str:
    return f"Rp {n:,.0f}".replace(",", ".")


def buat_pdf_rincian(path: str, satker: dict, pejabat_bendahara: dict, pejabat_ppk: dict,
                      surat_tugas, spd_hasil):
    c = canvas.Canvas(path, pagesize=A4)
    y = H - MARGIN

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(W / 2, y, "RINCIAN BIAYA PERJALANAN DINAS")
    y -= 10 * mm

    c.setFont("Helvetica", 9)
    x0 = MARGIN
    c.drawString(x0, y, f"LAMPIRAN SPD NOMOR : {surat_tugas.nomor_surat_tugas}")
    y -= 5 * mm
    c.drawString(x0, y, f"TANGGAL                  : {fmt_tgl_tulis_tangan(surat_tugas.tgl_tanda_tangan)}")
    y -= 5 * mm
    c.drawString(x0, y, f"NAMA                       : {spd_hasil.pegawai.nama}")
    y -= 8 * mm

    # Tabel rincian
    col_no = x0
    col_uraian = col_no + 10 * mm
    col_jumlah = W - MARGIN - 40 * mm
    col_ket = W - MARGIN - 0 * mm

    def header_tabel(yy):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(col_no, yy, "NO")
        c.drawString(col_uraian, yy, "RINCIAN BIAYA")
        c.drawRightString(col_jumlah + 30 * mm, yy, "JUMLAH")
        yy -= 3 * mm
        c.line(x0, yy, W - MARGIN, yy)
        return yy - 5 * mm

    y = header_tabel(y)
    c.setFont("Helvetica", 9)

    def baris(no, teks, nilai=None, indent=False, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 9)
        if no:
            c.drawString(col_no, y, str(no))
        c.drawString(col_uraian + (6 * mm if indent else 0), y, teks)
        if nilai is not None:
            c.drawRightString(col_jumlah + 30 * mm, y, _rp(nilai))
        y -= 5.5 * mm

    baris(1, "BIAYA TRANSPORT")
    baris(None, f"Transport {surat_tugas.asal} - {surat_tugas.tujuan} PP", spd_hasil.transport_tiket, indent=True)
    baris(None, f"Taksi {surat_tugas.asal} - {surat_tugas.tujuan} PP", spd_hasil.taksi, indent=True)

    baris(2, "UANG HARIAN")
    baris(None, f"{spd_hasil.hari} Hari x {_rp(spd_hasil.tarif_uang_harian)}", spd_hasil.uang_harian, indent=True)

    baris(3, "UANG PENGINAPAN")
    batas_inap = getattr(spd_hasil, "batas_sbm_inap", spd_hasil.tarif_inap)
    if spd_hasil.flag_lebih_sbm:
        uraian_inap = (
            f"{spd_hasil.malam_inap} Malam x {_rp(batas_inap)} (batas bayar; "
            f"tagihan aktual {_rp(spd_hasil.tarif_inap)})"
        )
    else:
        uraian_inap = f"{spd_hasil.malam_inap} Malam x {_rp(spd_hasil.tarif_inap)}"
    baris(None, uraian_inap, spd_hasil.uang_penginapan, indent=True)

    baris(4, "UANG REPRESENTASI")
    baris(None, f"{spd_hasil.hari} Hari x {_rp(spd_hasil.tarif_representasi)}", spd_hasil.uang_representasi, indent=True)

    baris(5, "BIAYA LAIN-LAIN", spd_hasil.biaya_lain)

    y -= 1 * mm
    c.line(x0, y, W - MARGIN, y)
    y -= 5 * mm
    baris(6, "JUMLAH   :", spd_hasil.jumlah, bold=True)

    y -= 3 * mm
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(col_uraian, y, f": {rupiah_terbilang(spd_hasil.jumlah)}")
    y -= 10 * mm

    if spd_hasil.flag_lebih_sbm:
        c.setFillColorRGB(0.7, 0, 0)
        peringatan = Paragraph(
            f"PERINGATAN: tagihan aktual {_rp(spd_hasil.tarif_inap)}/malam melebihi "
            f"batas SBM {_rp(batas_inap)}/malam. Nilai yang dibayar dibatasi ke batas SBM.",
            ParagraphStyle("peringatan_sbm", fontName="Helvetica-Bold", fontSize=8.5, leading=10),
        )
        _, warning_height = peringatan.wrap(W - 2 * MARGIN, 20 * mm)
        peringatan.drawOn(c, x0, y - warning_height)
        c.setFillColorRGB(0, 0, 0)
        y -= warning_height + 4 * mm

    c.setFont("Helvetica", 7.5)
    catatan = Paragraph(
        "Berdasarkan PMK 113/PMK.05/2012 pasal 36 : Pihak-pihak yang melakukan pemalsuan dokumen, "
        "menaikkan dari harga sebenarnya (mark up), dan/atau Perjalanan Dinas rangkap (dua kali atau lebih) "
        "dalam pertanggungjawaban Perjalanan Dinas yang berakibat kerugian yang diderita oleh negara, "
        "bertanggung jawab sepenuhnya atas seluruh tindakan yang dilakukan.",
        ParagraphStyle("catatan", fontName="Helvetica", fontSize=7.5, leading=9.5))
    pw, ph = catatan.wrap(W - 2 * MARGIN, 30 * mm)
    catatan.drawOn(c, x0, y - ph)
    y -= ph + 12 * mm

    # Blok tanda tangan
    col_width = (W - 2 * MARGIN) / 3
    signers = [
        (x0 + col_width / 2, "Bendahara Pengeluaran", pejabat_bendahara),
        (x0 + 1.5 * col_width, "Pejabat Pembuat Komitmen", pejabat_ppk),
        (x0 + 2.5 * col_width, "Pelaksana Perjalanan Dinas", None),
    ]
    c.setFont("Helvetica", 8)
    for center, title, _ in signers:
        c.drawCentredString(center, y, title)
    ppk_center = signers[1][0]
    c.setFont("Helvetica", 8)
    c.drawCentredString(
        ppk_center, y - 5 * mm,
        f"{satker['kota_kedudukan']}, {fmt_tgl_tulis_tangan(surat_tugas.tgl_tanda_tangan)}",
    )
    y -= 16 * mm
    c.setFont("Helvetica-Bold", 9)
    for center, _, pejabat in signers:
        nama = pejabat["nama"] if pejabat else spd_hasil.pegawai.nama
        c.drawCentredString(center, y, nama)
    y -= 4.5 * mm
    c.setFont("Helvetica", 9)
    for center, _, pejabat in signers:
        nip = pejabat["nip"] if pejabat else spd_hasil.pegawai.nip_nrp
        c.drawCentredString(center, y, f"NIP. {nip}")

    c.showPage()
    c.save()


def buat_pdf_kuitansi(path: str, satker: dict, pejabat_ppk: dict, pejabat_bendahara: dict,
                       pejabat_pelaksana_adm: dict,
                       surat_tugas, total_biaya: int, nomor_bukti: str = ""):
    c = canvas.Canvas(path, pagesize=A4)
    y = H - MARGIN
    x0 = MARGIN

    c.setFont("Helvetica-Bold", 11)
    c.drawString(x0, y, satker["nama_kementerian"])
    y -= 5 * mm
    c.drawString(x0, y, satker["nama_ditjen"])
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x0, y, satker["nama_satker_panjang"])
    y -= 4.5 * mm
    c.setFont("Helvetica", 8)
    c.drawString(x0, y, satker["alamat"])
    y -= 2 * mm
    c.line(x0, y, W - MARGIN, y)
    y -= 6 * mm

    # Blok kanan (Tahun Anggaran dst.) DI BAWAH kop, bukan di sampingnya,
    # supaya tidak pernah tumpang tindih dengan nama satker yang panjang.
    x_right = W - MARGIN - 65 * mm
    c.setFont("Helvetica", 9)
    c.drawString(x_right, y, f"Tahun Anggaran : {satker['tahun_anggaran']}")
    y -= 5 * mm
    c.drawString(x_right, y, f"Nomor Bukti      : {nomor_bukti}")
    y -= 5 * mm
    c.drawString(x_right, y, f"Mata Anggaran  : {surat_tugas.akun_anggaran}")
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W / 2, y, "KUITANSI")
    y -= 12 * mm

    label_style = ParagraphStyle("label", fontName="Helvetica", fontSize=9.5, leading=13)
    x_label = x0
    x_colon = x0 + 55 * mm
    x_isi = x_colon + 4 * mm
    isi_w = W - MARGIN - x_isi

    def baris(label, isi, tinggi_mm=6):
        nonlocal y
        c.setFont("Helvetica", 9.5)
        c.drawString(x_label, y, label)
        c.drawString(x_colon, y, ":")
        p_isi = Paragraph(isi, label_style)
        pw, ph = p_isi.wrap(isi_w, 30 * mm)
        p_isi.drawOn(c, x_isi, y - ph + 8)
        y -= max(tinggi_mm * mm, ph + 2)

    baris("Sudah terima dari",
          f"Pejabat Pembuat Komitmen {satker['nama_satker']} Satuan Kerja {satker['nama_satker']}",
          tinggi_mm=11)
    baris("Jumlah Uang", _rp(total_biaya))
    baris("Terbilang", rupiah_terbilang(total_biaya))
    baris("Untuk Pembayaran",
          f"Belanja Perjalanan Dinas untuk {surat_tugas.maksud_perjalanan} "
          f"ke {surat_tugas.tujuan}.", tinggi_mm=12)
    y -= 3 * mm
    baris("Berdasarkan SPD Nomor", f"1. {surat_tugas.nomor_surat_tugas}")
    baris("Tanggal", fmt_tgl_tulis_tangan(surat_tugas.tgl_tanda_tangan))
    baris("Untuk perjalanan dinas dari", f"{surat_tugas.asal} ke {surat_tugas.tujuan}")

    y -= 10 * mm
    col_width = (W - 2 * MARGIN) / 3
    centers = [MARGIN + col_width * (index + 0.5) for index in range(3)]
    c.setFont("Helvetica", 9)
    for center in centers:
        c.drawCentredString(
            center, y,
            f"{satker['kota_kedudukan']}, {fmt_tgl_tulis_tangan(surat_tugas.tgl_tanda_tangan)}",
        )
    y -= 5 * mm
    c.setFont("Helvetica", 8)
    c.drawCentredString(centers[0], y, "Bendahara Pengeluaran")
    c.drawCentredString(centers[1], y, pejabat_pelaksana_adm["jabatan_lengkap"])
    c.drawCentredString(centers[2], y, "Setuju dibebankan pada mata anggaran berkenaan")
    y -= 4.5 * mm
    c.drawCentredString(centers[2], y, "A.n Kuasa Pengguna Anggaran")
    y -= 4.5 * mm
    c.drawCentredString(centers[0], y, satker["nama_satker"])
    c.drawCentredString(centers[1], y, satker["nama_satker"])
    c.drawCentredString(centers[2], y, "Pejabat Pembuat Komitmen")
    y -= 4.5 * mm
    c.drawCentredString(centers[2], y, satker["nama_satker"])
    y -= 14 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(centers[0], y, pejabat_bendahara["nama"])
    c.drawCentredString(centers[1], y, pejabat_pelaksana_adm["nama"])
    c.drawCentredString(centers[2], y, pejabat_ppk["nama"])
    y -= 4.5 * mm
    c.setFont("Helvetica", 9)
    c.drawCentredString(centers[0], y, f"NIP. {pejabat_bendahara['nip']}")
    c.drawCentredString(centers[1], y, f"NIP. {pejabat_pelaksana_adm['nip']}")
    c.drawCentredString(centers[2], y, f"NIP. {pejabat_ppk['nip']}")

    c.showPage()
    c.save()
