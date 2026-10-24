# PEJADIN (prototype) - FastAPI + PostgreSQL (Supabase)

## 1. Siapkan Supabase
1. Buat project di supabase.com, simpan password database.
2. Klik **Connect** > tab **Connection string** > pilih **Session pooler** (port 5432), salin URI-nya.
   (Direct connection hanya IPv6; kalau koneksimu IPv4 pakai Session pooler.)
3. Password dengan karakter khusus harus di-URL-encode (@ jadi %40, # jadi %23, dst).

## 2. Jalankan di VS Code (Python 3.10+)
    cd backend
    copy .env.example .env      (Mac/Linux: cp .env.example .env)   lalu isi DATABASE_URL & SECRET
    pip install -r requirements.txt
    uvicorn main:app --reload

Buka http://localhost:8000. Saat pertama jalan, tabel (`backend/schema.sql`) dan data contoh dibuat otomatis di Supabase.
Login demo (password = username + 123): admin, operator, ppk, bendahara, pegawai. Segera ganti sebelum dipakai nyata.

## Deploy ke Vercel sebagai Services
1. Impor root repository (`pejadin`) sebagai satu project Vercel dengan Services aktif.
2. Konfigurasi `vercel.json` membuat service `app` untuk frontend dan service `backend` untuk FastAPI. Frontend publik pada `/`; API publik pada `/api/*`. Rewrite API harus berada sebelum rewrite catch-all frontend.
3. Tambahkan environment variables `DATABASE_URL` (Supabase Session pooler, port 5432) dan `SECRET` pada project Vercel. Jangan unggah `backend/.env`.
4. Deploy. Kedua service menggunakan domain yang sama. Frontend memanggil API melalui path `/api/...`; karena komunikasi berlangsung lewat browser dan rewrite publik, tidak diperlukan service binding.
5. Skema inisialisasi ada di `backend/schema.sql`, dalam root service backend agar dapat dipaketkan saat deploy.

## 3. Kompatibilitas API sesuai desain teknis
- Endpoint legacy tetap dipertahankan: `/api/*`
- Endpoint versi formal mengikuti desain teknis: `/api/v1/*`
- Contoh auth: `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- Base API untuk master data, ST, SPD, dokumen, dan laporan juga tersedia pada prefix `/api/v1`
- Referensi golongan ke pangkat tersedia bagi pengguna terautentikasi melalui `GET /api/v1/ref/golongan-pangkat`.
- Antarmuka memakai tema Kementerian Pekerjaan Umum dan aset lambang yang disediakan pengguna pada `frontend/assets/logo-kementerian-pu.png`; login dua kolom beralih ke satu kolom dan sidebar menjadi drawer pada layar kecil
- Login otomatis mencatat `last_login` dan memperbarui `updated_at`, dan trigger database menjaga timestamp audit trail tetap konsisten
- Alur ST tahap 1: OPERATOR dapat menerbitkan langsung dari `DRAFT` agar surat siap dicetak, atau tetap mengajukan ke PPK melalui `DIAJUKAN`. PPK tetap dapat menerbitkan pengajuan, mengembalikan ke `DRAFT`, atau membatalkan ST berstatus `DIAJUKAN` dengan alasan. ST terbit dapat ditandai `SELESAI`.
- Kewenangan alur ST: OPERATOR membuat/mengubah draft, mengajukan ke PPK, atau menerbitkan langsung; PPK menerbitkan pengajuan serta mengembalikan/membatalkan; ADMIN hanya mengelola sistem dan dapat melihat Monitoring/cetak tanpa mengubah atau memproses ST.
- Draft dapat diedit OPERATOR sebelum diterbitkan atau diajukan; tanggal/provinsi hanya dapat diubah setelah seluruh pelaksana dihapus. Pegawai nonaktif tidak tersedia untuk dipilih sebagai pelaksana.
- Audit Trail mencatat nilai sebelum/sesudah perubahan; timestamp disimpan dalam UTC dan ditampilkan dalam WIB. NIP dan nomor rekening disamarkan di detail audit.
- Tanggal ST harus berformat `YYYY-MM-DD` dengan tanggal kembali tidak mendahului tanggal berangkat; tanggal surat dan tanda tangan wajib diisi dan tidak boleh setelah tanggal berangkat; maksud, tujuan, dan jenis kuitansi UP/LS wajib valid; jumlah hari pelaksana dihitung inklusif dari tanggal ST dan jumlah malam menginap otomatis dihitung sebagai jumlah hari dikurangi satu. Keduanya hanya ditampilkan pada form dan nilai berbeda yang dikirim melalui API ditolak; nilai biaya tidak boleh negatif.
- Format respons error API konsisten sebagai `{"error":{"code":"V3","message":"..."}}`; validasi input mengembalikan HTTP 422 dan kode validasi mengikuti V1–V9.

## Mesin hitung dan dokumen PDF
- Kalkulasi SPD berjalan di backend memakai tarif SBM tahun/provinsi dari referensi; hasil kalkulasi disimpan pada SPD sebagai snapshot dan PDF membaca snapshot tersebut. Tagihan penginapan aktual tetap dicatat, tetapi jumlah yang dihitung untuk dibayar dibatasi oleh tarif SBM per malam sesuai eselon/golongan.
- Endpoint PDF: `GET /api/v1/st/{id}/pdf/{jenis}`. Jenis yang tersedia: `st`, `st_lampiran`, `spd`, `rincian`, `kuitansi`, `nominatif`, `sptjb`, `laporan`, `riil`, dan `lengkap` (satu berkas gabungan).
- Pilihan beberapa dokumen tersedia melalui `POST /api/v1/st/{id}/pdf/pilihan` dengan body `{"jenis":["st","spd"],"format":"zip"}` atau `"format":"pdf"`. Format `zip` berisi satu PDF per jenis dokumen; format `pdf` menggabungkan dokumen terpilih menjadi satu PDF. Pengguna PEGAWAI hanya dapat memilih SPD, rincian biaya, atau pengeluaran riil miliknya.
- Di halaman **Cetak Dokumen PDF**, tekan **Unduh/Cetak Dokumen** pada Surat Tugas untuk membuka pilihan dokumen dan format dalam pop-up. PDF gabungan ditampilkan untuk diperiksa sebelum diunduh; ZIP menampilkan daftar isi terlebih dahulu dan baru diunduh setelah tombol unduh dipilih.
- PDF hanya tersedia untuk ST berstatus `TERBIT` atau `SELESAI`. Berkas hasil cetak dicatat pada audit dan tabel `dokumen_terbit`.
- Isi Identitas Satker, DIPA, rekening, nomor SPTJB, pejabat penanda tangan, tanggal surat/tanda tangan, serta data pegawai sebelum mencetak. SPD memerlukan pangkat dan tingkat biaya; SPTJB memerlukan nilai PPN/PPh aktual yang diinput, dan Daftar Pengeluaran Riil memerlukan nilai riil yang dinyatakan secara eksplisit.
- `reportlab` dan `pypdf` tercantum di `backend/requirements.txt` dan dipasang bersama dependensi backend.

## Catatan
- Semua tabel memakai Row Level Security tanpa policy, jadi tidak bisa diakses lewat Data API/anon key Supabase. Hanya backend (role postgres) yang bisa membaca/menulis.
- Profil Satker terstruktur per tahun disimpan di `satker_tahunan`, termasuk `tanggal_dipa` bertipe DATE dan `kode_akun_belanja`. Saat kompatibilitas dijalankan, nilai lama dari `satker(k,v)` disalin sebagai profil TA 2026; endpoint key-value tetap tersedia dan memperbarui kedua tabel selama transisi.
- Relasi SPD ke pegawai memakai foreign key. Migrasi menegakkan foreign key untuk referensi baru dan memberi peringatan bila masih ada baris lama yatim; baris tersebut tidak dihapus atau diubah otomatis.
- Pembatasan laju per IP berlaku untuk login (5 permintaan/menit) dan pembuatan PDF paket lengkap (3 permintaan/menit). Penghitung ini berada di memori proses aplikasi.
- Jangan commit file .env atau file referensi klien yang memuat NIP/rekening. Seed pada database baru berisi data contoh; database uji saat ini memakai referensi klien. Tiga kelompok NIP yang konflik dikecualikan, dan 120 pegawai hasil impor belum memiliki tingkat biaya perjalanan sehingga data tersebut harus dilengkapi sebelum dipakai untuk SPD/PDF.
- backend/main.py = API, mesin hitung, validasi V1-V9, alur status, audit, cetak. frontend/index.html = antarmuka. design/ = acuan Stitch.
