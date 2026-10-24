"""Helper bersama untuk semua generator PDF (padanan format PMK 113/2012)."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

W, H = A4
MARGIN = 20 * mm

_BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def fmt_tgl(d) -> str:
    """P10: tanggal -> format Indonesia, mis. '13 Mei 2026'."""
    if d is None:
        return "-"
    return f"{d.day} {_BULAN[d.month]} {d.year}"


def fmt_tgl_tulis_tangan(d) -> str:
    if d is None:
        return "...................................."
    return fmt_tgl(d)


def fmt_periode(d1, d2) -> str:
    """P10: '13 Mei 2026 s/d 14 Mei 2026'; bila 1 hari cukup satu tanggal."""
    if d1 is None or d2 is None:
        return "-"
    if d1 == d2:
        return fmt_tgl(d1)
    return f"{fmt_tgl(d1)} s/d {fmt_tgl(d2)}"


def rp(n: int) -> str:
    return f"Rp {n:,.0f}".replace(",", ".")


def angka(n: int) -> str:
    return f"{n:,.0f}".replace(",", ".")


def draw_kop_surat(c, satker: dict, y_top: float) -> float:
    """Kop surat kementerian/ditjen/satker di kiri atas. Return y setelah garis bawah."""
    x = MARGIN
    y = y_top
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, satker["nama_kementerian"])
    y -= 5 * mm
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


def paragraf(c, text: str, x: float, y: float, width: float, font="Helvetica", size=9, leading=12) -> float:
    """Gambar Paragraph pada (x, y) sebagai TOP-LEFT; return y baru (di bawah teks)."""
    style = ParagraphStyle("p", fontName=font, fontSize=size, leading=leading)
    p = Paragraph(text, style)
    pw, ph = p.wrap(width, 200 * mm)
    p.drawOn(c, x, y - ph)
    return y - ph


def blok_paraf_tiga(c, y: float, pejabat_ppk: dict, pejabat_kabag: dict, pejabat_sekditjen: dict) -> float:
    """Blok 'Paraf' 3 kolom: PPK / Kabag / Sekditjen (dipakai ST & ST_LAMPIRAN)."""
    x0 = MARGIN
    col_w = (W - 2 * MARGIN) / 3
    c.setFont("Helvetica", 8.5)
    c.drawString(x0, y, "Paraf")
    y -= 5 * mm
    c.drawString(x0, y, "PPK Setditjen SDA")
    c.drawString(x0 + col_w, y, "Kabag Keuangan, PBMN, & PBP")
    c.drawString(x0 + 2 * col_w, y, "Sekretaris Direktorat Jenderal SDA")
    y -= 16 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x0, y, pejabat_ppk["nama"])
    c.drawString(x0 + col_w, y, pejabat_kabag["nama"])
    c.drawString(x0 + 2 * col_w, y, pejabat_sekditjen["nama"])
    return y - 5 * mm
