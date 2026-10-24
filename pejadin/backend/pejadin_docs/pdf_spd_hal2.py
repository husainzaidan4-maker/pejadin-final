"""
Generator PDF: SPD halaman 2 - pengesahan tiba/berangkat (butir I-VIII).
Padanan sheet 'SPD_HAL2'. Butir I diisi otomatis (data keberangkatan awal,
ditandatangani PPK). Butir II-V dikosongkan untuk ditandatangani manual oleh
pejabat di lokasi tujuan (sesuai catatan spec: "dikosongkan untuk
ditandatangani manual"). Butir VI = pengesahan tiba kembali di tempat asal.
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from .pdf_common import W, H, MARGIN, fmt_tgl


def buat_pdf_spd_hal2(path: str, satker: dict, pejabat_ppk: dict, pejabat_pengesah: dict,
                       surat_tugas, spd_hasil):
    c = canvas.Canvas(path, pagesize=A4)
    x0 = MARGIN
    x_label2 = W / 2
    y = H - MARGIN

    c.setFont("Helvetica", 8.5)
    c.drawCentredString(W / 2, y, "Peraturan Menteri Keuangan Nomor : 113/PMK.05/2012")
    y -= 4 * mm
    c.drawCentredString(W / 2, y, "Tentang")
    y -= 4 * mm
    c.drawCentredString(W / 2, y, "Perjalanan Dinas Jabatan Dalam Negeri, Bagi Pejabat Negara, "
                                    "Pegawai Negeri, dan Pegawai Tidak Tetap.")
    y -= 10 * mm

    def label_isi(x, yy, label, isi, lebar_label=32 * mm):
        c.setFont("Helvetica", 9)
        c.drawString(x, yy, label)
        c.drawString(x + lebar_label, yy, f": {isi}")

    # Butir I - Berangkat (terisi otomatis, TTD PPK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(x0, y, "I.")
    label_isi(x0 + 8 * mm, y, "Berangkat dari", satker["kota_kedudukan"])
    y -= 4.5 * mm
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(x0 + 8 * mm + 32 * mm, y, "(Tempat kedudukan)")
    y -= 5 * mm
    label_isi(x0 + 8 * mm, y, "Ke", surat_tugas.tujuan)
    y -= 4.5 * mm
    label_isi(x0 + 8 * mm, y, "Pada tanggal", fmt_tgl(surat_tugas.tgl_berangkat))
    y -= 8 * mm
    c.setFont("Helvetica", 9)
    c.drawString(x0 + 8 * mm, y, "Pejabat Pembuat Komitmen")
    y -= 15 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x0 + 8 * mm, y, pejabat_ppk["nama"])
    y -= 4.5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(x0 + 8 * mm, y, f"NIP. {pejabat_ppk['nip']}")
    y -= 10 * mm

    # Butir II - V: kosong untuk diisi manual di lokasi tujuan
    romawi = ["II", "III", "IV", "V"]
    for r in romawi:
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(x0, y, f"{r}.")
        c.setFont("Helvetica", 9)
        c.drawString(x0 + 8 * mm, y, "Tiba di")
        c.drawString(x0 + 8 * mm + 22 * mm, y, ": ……………………………")
        c.drawString(x_label2, y, "Berangkat dari")
        c.drawString(x_label2 + 28 * mm, y, ": ……………………………")
        y -= 4.5 * mm
        c.drawString(x0 + 8 * mm, y, "Pada Tanggal")
        c.drawString(x0 + 8 * mm + 22 * mm, y, ": ……………………………")
        c.drawString(x_label2, y, "Ke")
        c.drawString(x_label2 + 28 * mm, y, ": ……………………………")
        y -= 4.5 * mm
        c.drawString(x0 + 8 * mm, y, "Kepala")
        c.drawString(x0 + 8 * mm + 22 * mm, y, ":")
        c.drawString(x_label2, y, "Pada Tanggal")
        c.drawString(x_label2 + 28 * mm, y, ": ……………………………")
        y -= 4.5 * mm
        c.drawString(x_label2, y, "Kepala")
        c.drawString(x_label2 + 28 * mm, y, ":")
        y -= 12 * mm
        c.drawString(x0 + 8 * mm, y, "( ……………………….….……………………...)")
        c.drawString(x_label2, y, "( ……………………….….……………………...)")
        y -= 4.5 * mm
        c.drawString(x0 + 8 * mm, y, "NIP.")
        c.drawString(x_label2, y, "NIP.")
        y -= 8 * mm

    # Butir VI - tiba kembali di tempat asal, diperiksa PPK
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(x0, y, "VI.")
    label_isi(x0 + 8 * mm, y, "Tiba di", satker["kota_kedudukan"])
    isi_kanan_w = W - MARGIN - x_label2
    c.setFont("Helvetica", 8)
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    ket = Paragraph("Telah diperiksa dengan keterangan bahwa perjalanan tersebut atas perintah "
                     "dan semata-mata untuk kepentingan jabatan dalam waktu yang sesingkat-singkatnya.",
                     ParagraphStyle("k", fontName="Helvetica", fontSize=8, leading=10))
    pw, ph = ket.wrap(isi_kanan_w, 20 * mm)
    ket.drawOn(c, x_label2, y - ph + 6)
    y -= max(5 * mm, ph)
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(x0 + 8 * mm + 32 * mm, y, "(Tempat kedudukan)")
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    label_isi(x0 + 8 * mm, y, "Pada Tanggal", "……………………………")
    y -= 10 * mm

    c.drawString(x0 + 8 * mm, y, "Pejabat Yang Berwenang/Pejabat Lain Yang Ditunjuk")
    c.drawString(x_label2, y, "Pejabat Pembuat Komitmen")
    y -= 4.5 * mm
    c.drawString(x0 + 8 * mm, y, satker["nama_satker"])
    c.drawString(x_label2, y, satker["nama_satker"])
    y -= 15 * mm
    c.setFont("Helvetica", 8.5)
    c.drawString(x0 + 8 * mm, y, pejabat_pengesah["jabatan_lengkap"])
    c.drawString(x_label2, y, pejabat_ppk.get("jabatan_lengkap") or pejabat_ppk["jabatan"])
    y -= 16 * mm
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x0 + 8 * mm, y, pejabat_pengesah["nama"])
    c.drawString(x_label2, y, pejabat_ppk["nama"])
    y -= 4.5 * mm
    c.setFont("Helvetica", 8.5)
    c.drawString(x0 + 8 * mm, y, f"NIP. {pejabat_pengesah['nip']}")
    c.drawString(x_label2, y, f"NIP. {pejabat_ppk['nip']}")

    c.showPage()
    c.save()
