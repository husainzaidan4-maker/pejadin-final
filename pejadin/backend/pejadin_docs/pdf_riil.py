"""Generator PDF: Daftar Pengeluaran Riil. Padanan sheet 'RIIL'. TTD: pelaksana + PPK."""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from .pdf_common import W, H, MARGIN, fmt_tgl, fmt_tgl_tulis_tangan, rp, paragraf
from .terbilang import rupiah_terbilang


def buat_pdf_riil(path: str, satker: dict, pejabat_ppk: dict, surat_tugas, spd_hasil,
                   jumlah_riil: int = None):
    """jumlah_riil harus berasal dari data pengeluaran aktual yang diinput."""
    if jumlah_riil is None:
        raise ValueError("jumlah_riil harus diberikan secara eksplisit")

    c = canvas.Canvas(path, pagesize=A4)
    x0 = MARGIN
    y = H - MARGIN
    pegawai = spd_hasil.pegawai

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(W / 2, y, "DAFTAR PENGELUARAN RIIL")
    y -= 10 * mm

    c.setFont("Helvetica", 9.5)
    c.drawString(x0, y, "Yang bertanda tangan di bawah ini;")
    y -= 8 * mm
    c.drawString(x0, y, "Nama")
    c.drawString(x0 + 30 * mm, y, f": {pegawai.nama}")
    y -= 4.5 * mm
    c.drawString(x0, y, "NIP/NRP")
    c.drawString(x0 + 30 * mm, y, f": {pegawai.nip_nrp}")
    y -= 4.5 * mm
    c.drawString(x0, y, "Jabatan")
    c.drawString(x0 + 30 * mm, y, f": {pegawai.jabatan}")
    y -= 8 * mm

    y = paragraf(c, f"Berdasarkan Surat Perjalanan Dinas (SPD) Nomor {surat_tugas.nomor_surat_tugas} "
                    f"tanggal {fmt_tgl_tulis_tangan(surat_tugas.tgl_tanda_tangan)} dengan ini kami menyatakan "
                    f"dengan sesungguhnya bahwa:", x0, y, W - 2 * MARGIN, size=9.5, leading=12.5)
    y -= 5 * mm

    y = paragraf(c, "1. Biaya transport pegawai dan/atau penginapan di bawah ini yang tidak "
                    "dapat diperoleh bukti-bukti pengeluaran, meliputi:", x0, y, W - 2 * MARGIN,
                 size=9.5, leading=12.5)
    y -= 6 * mm

    # Tabel sederhana
    x_no = x0
    x_uraian = x0 + 10 * mm
    x_jumlah = W - MARGIN - 35 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_uraian, y, "Uraian")
    c.drawRightString(W - MARGIN, y, "Jumlah")
    y -= 2 * mm
    c.line(x0, y, W - MARGIN, y)
    y -= 5 * mm

    c.setFont("Helvetica", 9)
    c.drawString(x_no, y, "1")
    y2 = paragraf(c, f"Biaya Transport dari {surat_tugas.asal} ke {surat_tugas.tujuan} "
                     f"pada tanggal {fmt_tgl(surat_tugas.tgl_berangkat)}.",
                  x_uraian, y + 3 * mm, x_jumlah - x_uraian - 4 * mm, size=9, leading=11.5)
    c.drawRightString(W - MARGIN, y, rp(jumlah_riil))
    y = min(y2, y) - 5 * mm

    c.line(x0, y, W - MARGIN, y)
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_uraian, y, "Jumlah")
    c.drawRightString(W - MARGIN, y, rp(jumlah_riil))
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(x_uraian, y, f"Terbilang : {rupiah_terbilang(jumlah_riil)}")
    y -= 8 * mm

    y = paragraf(c, "2. Jumlah uang tersebut pada angka 1 di atas benar-benar dikeluarkan untuk "
                    "pelaksanaan perjalanan dinas dimaksud dan apabila dikemudian hari terdapat "
                    "kelebihan pembayaran, kami bersedia untuk menyetorkan kelebihan tersebut ke "
                    "Kas Negara.", x0, y, W - 2 * MARGIN, size=9.5, leading=12.5)
    y -= 6 * mm
    y = paragraf(c, "Demikian pernyataan ini kami buat dengan sebenarnya, untuk dipergunakan "
                    "sebagaimana perlunya.", x0, y, W - 2 * MARGIN, size=9.5, leading=12.5)
    y -= 10 * mm

    xkanan = W - MARGIN - 65 * mm
    c.setFont("Helvetica", 9)
    c.drawString(xkanan, y, f"{satker['kota_kedudukan']}, {fmt_tgl_tulis_tangan(surat_tugas.tgl_tanda_tangan)}")
    y -= 5 * mm
    c.drawString(x0, y, "Mengetahui/ Menyetujui")
    c.drawString(xkanan, y, "Pelaksana SPD")
    y -= 4.5 * mm
    c.drawString(x0, y, "Pejabat Pembuat Komitmen Satuan Kerja")
    y -= 4.5 * mm
    c.drawString(x0, y, satker["nama_satker"])
    y -= 18 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x0, y, pejabat_ppk["nama"])
    c.drawString(xkanan, y, pegawai.nama)
    y -= 4.5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(x0, y, f"NIP. {pejabat_ppk['nip']}")
    c.drawString(xkanan, y, f"NIP. {pegawai.nip_nrp}")

    c.showPage()
    c.save()
