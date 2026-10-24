"""
Generator PDF: Surat Perjalanan Dinas (SPD) halaman 1.
Format mengikuti Lampiran II PMK 113/PMK.05/2012 (padanan sheet 'SPD').
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .pdf_common import fmt_tgl_tulis_tangan

W, H = A4
MARGIN = 20 * mm

STYLE_NORMAL = ParagraphStyle("normal", fontName="Helvetica", fontSize=9, leading=12)
STYLE_BOLD = ParagraphStyle("bold", fontName="Helvetica-Bold", fontSize=9, leading=12)


def _p(text, style=STYLE_NORMAL):
    return Paragraph(text, style)


def draw_kop_surat(c: canvas.Canvas, satker: dict, y_top: float):
    """Kop surat kementerian/ditjen/satker di kiri atas."""
    x = MARGIN
    y = y_top
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, satker["nama_kementerian"])
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, satker["nama_ditjen"])
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, satker["nama_satker_panjang"])
    y -= 4.5 * mm
    c.setFont("Helvetica", 8)
    c.drawString(x, y, satker["alamat"])
    y -= 2 * mm
    c.line(x, y, W - MARGIN, y)
    return y - 4 * mm


def buat_pdf_spd(path: str, satker: dict, pejabat_ppk: dict, surat_tugas, spd_hasil, nomor_lembar: int = 1):
    """
    surat_tugas: business_rules.SuratTugas
    spd_hasil: business_rules.SPDHasil (untuk 1 pelaksana)
    """
    c = canvas.Canvas(path, pagesize=A4)

    y_kop = H - MARGIN
    y_kop = draw_kop_surat(c, satker, y_kop)

    # Blok rujukan Lampiran II PMK - DI BAWAH kop (bukan di sampingnya) supaya
    # tidak pernah tumpang tindih walau nama satker/kementerian panjang.
    x_right = W - MARGIN - 70 * mm
    y_ref = y_kop
    c.setFont("Helvetica", 8)
    for line in [
        "LAMPIRAN II",
        "PERATURAN MENTERI KEUANGAN REPUBLIK INDONESIA",
        "NOMOR : 113 / PMK.05 / 2012",
        "TENTANG",
    ]:
        c.drawString(x_right, y_ref, line)
        y_ref -= 3.6 * mm
    p = Paragraph("PERJALANAN DINAS DALAM NEGERI BAGI PEJABAT NEGARA, "
                   "PEGAWAI NEGERI, DAN PEGAWAI TIDAK TETAP",
                   ParagraphStyle("ref", fontName="Helvetica", fontSize=7.5, leading=9))
    pw, ph = p.wrap(70 * mm, 20 * mm)
    p.drawOn(c, x_right, y_ref - ph + 3)
    y_ref -= ph + 3 * mm

    c.setFont("Helvetica", 8)
    c.drawString(x_right, y_ref, f"Lembar Ke        : {nomor_lembar}")
    y_ref -= 4 * mm
    c.drawString(x_right, y_ref, "Kode No.          :")
    y_ref -= 4 * mm
    c.drawString(x_right, y_ref, f"Nomor SPPD    : {surat_tugas.nomor_surat_tugas}")
    y_ref -= 4 * mm

    # Judul dimulai di bawah blok rujukan
    y = y_ref - 6 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(W / 2, y, "SURAT PERJALANAN DINAS (SPD)")
    y -= 8 * mm

    # Tabel bernomor 1-10
    col_no_w = 7 * mm
    col_label_w = 68 * mm
    col_colon_w = 4 * mm
    x0 = MARGIN
    x_no = x0
    x_label = x_no + col_no_w
    x_colon = x_label + col_label_w
    x_isi = x_colon + col_colon_w
    label_w = col_label_w - 2 * mm
    isi_w = W - MARGIN - x_isi

    STYLE_LABEL = ParagraphStyle("label", fontName="Helvetica", fontSize=9, leading=11)

    def baris(no, label, isi, tinggi_mm=6, style_isi=STYLE_NORMAL):
        nonlocal y
        c.setFont("Helvetica", 9)
        baseline_no = y - 3.2 * mm
        if no is not None:
            c.drawString(x_no, baseline_no, str(no) + ".")
        c.drawString(x_colon, baseline_no, ":")

        p_label = Paragraph(label, STYLE_LABEL)
        lw, lh = p_label.wrap(label_w, 30 * mm)

        ph = 0
        if isi:
            p_isi = Paragraph(isi, style_isi)
            iw, ph = p_isi.wrap(isi_w, 40 * mm)

        tinggi = max(tinggi_mm * mm, lh, ph)
        # gambar dari atas baris (posisi y saat ini adalah TOP baris, bukan baseline)
        p_label.drawOn(c, x_label, y - lh + 1)
        if isi:
            p_isi.drawOn(c, x_isi, y - ph + 1)
        y -= tinggi

    pegawai = spd_hasil.pegawai
    nama_satker_line = (f"{satker['nama_satker']}<br/>"
                         f"Satuan Kerja {satker['nama_satker']}<br/>"
                         f"{satker['nama_kementerian']}")
    baris(1, "Pejabat Pembuat Komitmen", nama_satker_line, tinggi_mm=13)
    baris(2, "Nama / NIP. Pegawai yang melaksanakan perjalanan dinas",
          f"{pegawai.nama} / {pegawai.nip_nrp}")
    baris("3a", "a. Pangkat dan golongan", f"{pegawai.pangkat} &nbsp;&nbsp; {pegawai.golongan}")
    baris(None, "b. Jabatan / Instansi", pegawai.jabatan)
    baris(None, "c. Tingkat Biaya Perjalanan Dinas", pegawai.tingkat_biaya or "-")
    baris(4, "Maksud Perjalanan Dinas", surat_tugas.maksud_perjalanan, tinggi_mm=10)
    baris(5, "Alat angkutan yang dipergunakan", surat_tugas.alat_angkutan or "-")
    baris("6a", "a. Tempat berangkat", surat_tugas.asal)
    baris(None, "b. Tempat tujuan", surat_tugas.tujuan)
    baris("7a", "a. Lamanya perjalanan dinas", f"{spd_hasil.hari} Hari")
    baris(None, "b. Tanggal berangkat", _fmt_tgl(surat_tugas.tgl_berangkat))
    baris(None, "c. Tgl. harus kembali/tiba di tempat baru *)", _fmt_tgl(surat_tugas.tgl_kembali))
    baris(8, "Pengikut", "-")
    baris(9, "Pembebanan Anggaran", "", tinggi_mm=5)
    baris(None, "a. Instansi", satker["nama_satker"])
    baris(None, "b. Akun", surat_tugas.akun_anggaran)
    baris(10, "Keterangan lain-lain",
          f"NOMOR : {surat_tugas.nomor_surat_tugas} &nbsp;&nbsp; Tanggal {fmt_tgl_tulis_tangan(surat_tugas.tanggal_surat_tugas)}",
          tinggi_mm=10)

    y -= 2 * mm  # dari "top baris" ke baseline teks berikutnya
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(x0, y, "*) Coret yang tidak perlu")
    y -= 10 * mm

    # Blok tanda tangan PPK (kanan)
    xsig = W - MARGIN - 75 * mm
    c.setFont("Helvetica", 9)
    c.drawString(xsig, y, f"Dikeluarkan di : {satker['kota_kedudukan']}")
    y -= 5 * mm
    c.drawString(xsig, y, f"Tanggal          : {fmt_tgl_tulis_tangan(surat_tugas.tgl_tanda_tangan)}")
    y -= 8 * mm
    c.drawString(xsig, y, "Pejabat Pembuat Komitmen")
    y -= 4.5 * mm
    c.drawString(xsig, y, satker["nama_satker"])
    y -= 18 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(xsig, y, pejabat_ppk["nama"])
    y -= 4.5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(xsig, y, f"NIP. {pejabat_ppk['nip']}")

    c.showPage()
    c.save()


def _fmt_tgl(d) -> str:
    if d is None:
        return "-"
    bulan = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
             "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    return f"{d.day} {bulan[d.month]} {d.year}"
