"""
Cetak massal: gabungkan beberapa file PDF menjadi satu PDF utuh.
Padanan kebutuhan di spec baris 179: 'satu tombol menghasilkan SATU PDF
gabungan berisi seluruh dokumen untuk semua pelaksana'.
"""
from pypdf import PdfWriter


def gabungkan_pdf(daftar_path: list, path_output: str):
    writer = PdfWriter()
    for p in daftar_path:
        writer.append(p)
    with open(path_output, "wb") as f:
        writer.write(f)
