"""
Utilitas: angka -> terbilang Bahasa Indonesia (Rupiah).
Padanan Excel: sheet TERBILANG.
Aturan P9 di SPEC_WEBAPP.
"""

_SATUAN = [
    "", "satu", "dua", "tiga", "empat", "lima",
    "enam", "tujuh", "delapan", "sembilan",
]

_BELASAN = [
    "sepuluh", "sebelas", "dua belas", "tiga belas", "empat belas",
    "lima belas", "enam belas", "tujuh belas", "delapan belas", "sembilan belas",
]


def _angka_ke_kata(n: int) -> str:
    """Konversi bilangan bulat non-negatif < 10^15 ke kata-kata (tanpa 'rupiah')."""
    if n < 0:
        raise ValueError("terbilang hanya menerima bilangan non-negatif")
    if n == 0:
        return "nol"

    def bagi_tiga_angka(x: int) -> str:
        """0..999 -> kata."""
        hasil = []
        ratusan = x // 100
        sisa = x % 100
        if ratusan == 1:
            hasil.append("seratus")
        elif ratusan > 1:
            hasil.append(_SATUAN[ratusan] + " ratus")
        if 10 <= sisa < 20:
            hasil.append(_BELASAN[sisa - 10])
        else:
            puluhan = sisa // 10
            satuan = sisa % 10
            if puluhan == 1:
                pass  # sudah ditangani oleh _BELASAN di atas untuk 10-19
            elif puluhan > 1:
                hasil.append(_SATUAN[puluhan] + " puluh")
            if satuan > 0 and not (10 <= sisa < 20):
                hasil.append(_SATUAN[satuan])
        return " ".join(hasil).strip()

    tingkat = [
        (10 ** 12, "triliun"),
        (10 ** 9, "miliar"),
        (10 ** 6, "juta"),
        (10 ** 3, "ribu"),
        (1, ""),
    ]

    sisa = n
    bagian = []
    for nilai, label in tingkat:
        jumlah = sisa // nilai
        sisa = sisa % nilai
        if jumlah == 0:
            continue
        if nilai == 1000 and jumlah == 1:
            # 'seribu', bukan 'satu ribu'
            bagian.append("seribu")
        else:
            teks = bagi_tiga_angka(jumlah)
            if label:
                teks = f"{teks} {label}"
            bagian.append(teks)

    return " ".join(bagian).strip()


def angka_ke_terbilang(n: int) -> str:
    """Bilangan bulat -> terbilang (tanpa satuan mata uang), huruf kecil kecuali huruf awal."""
    if n < 0:
        return "minus " + _angka_ke_kata(abs(n))
    return _angka_ke_kata(n)


def rupiah_terbilang(n: int) -> str:
    """
    Contoh: 1280000 -> 'Satu juta dua ratus delapan puluh ribu rupiah'
    Huruf pertama kapital, sisanya huruf kecil, diakhiri kata 'rupiah'.
    """
    kata = angka_ke_terbilang(int(round(n)))
    kata = f"{kata} rupiah"
    return kata[0].upper() + kata[1:]


if __name__ == "__main__":
    tests = {
        0: "Nol rupiah",
        1: "Satu rupiah",
        11: "Sebelas rupiah",
        21: "Dua puluh satu rupiah",
        100: "Seratus rupiah",
        1000: "Seribu rupiah",
        1120000: "Satu juta seratus dua puluh ribu rupiah",
        1280000: "Satu juta dua ratus delapan puluh ribu rupiah",
        1890000: "Satu juta delapan ratus sembilan puluh ribu rupiah",
    }
    for n, expected in tests.items():
        got = rupiah_terbilang(n)
        status = "OK" if got == expected else "MISMATCH"
        print(f"{status:9s} {n:>10} -> {got!r} (expected {expected!r})")
