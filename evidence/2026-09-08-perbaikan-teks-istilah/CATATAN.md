# Evidence — Perbaikan Teks & Istilah UI (arahan Bu Ariana, meeting 8 Sept 2026)

Tanggal pengujian: 8 September 2026

## Ringkasan perubahan

1. Nama aplikasi: `config.APP_NAME = "UPStock"` — konstanta terpusat (Single Source of Truth),
   dipakai di `app.py` (page_title & sidebar), bukan hardcode berulang.
2. Judul tab browser: `"Kelola Stok UMKM Bareng UPStock"`.
3. Sidebar: baris nama besar `"UPStock"` + baris subjudul kecil `"Bantu UMKM Kelola Stok"` —
   dua baris terpisah, tanpa tanda pisah.
4. Elemen "Model Terbaik" (nama model teknis seperti XGBoost) dihapus dari sidebar — terpisah
   dari T-19 (kartu akurasi 92%), lokasi yang belum pernah disentuh sebelumnya.
5. "Horizon" diganti 2 istilah beda konteks: sidebar (info pasif) jadi `"Rentang Waktu"`,
   dropdown interaktif Perkiraan Penjualan jadi `"Rentang Waktu Prediksi"`.
6. `"Resep / Bill of Materials"` jadi `"Resep / Daftar Kebutuhan Bahan"`.
7. **Temuan tak terduga, ditemukan & diperbaiki dalam scope sama** (dilaporkan sebelum
   eksekusi): tanggal yang dirender lewat `strftime()`/Plotly hover default-nya render nama
   hari/bulan Inggris (`Saturday`, `Wed`, `Sep`) karena locale sistem default, BUKAN string
   hardcode. Diperbaiki dengan fungsi mapping manual `ui.tanggal_id()` (bukan
   `locale.setlocale("id_ID")` — rapuh, sering tak terpasang di server/Windows, berisiko
   `LookupError` saat deploy) dipakai di 3 lokasi: `views/forecasting.py` (tabel Rincian per
   Hari), `views/inventory.py` (tabel bahan baku expander), `components/charts.py` (hover
   grafik, via `customdata` karena Plotly hovertemplate `%{x|...}` juga Inggris). Sumbu-x
   grafik (`components/charts.py`) diganti format numerik `%d/%m` — locale-independent,
   menghindari nama bulan Inggris tanpa perlu registrasi locale Plotly.

## Pengecekan tanda pisah ("-"/"—")

Grep menyeluruh terhadap SEMUA teks UI baru/diubah tugas ini (bukan kode existing tak
tersentuh) — NOL tanda pisah ditemukan. Komentar kode Python (`# ... -- alasan`) dikecualikan
karena tak dirender ke layar, sesuai gaya penulisan komentar proyek ini sejak awal.

## Pengujian UI end-to-end (streamlit run, browser)

1. **Judul tab browser**: `"Kelola Stok UMKM Bareng UPStock"` — terkonfirmasi.
2. **Ringkasan Operasional**:
   - Sidebar: `"UPStock"` (baris besar) + `"Bantu UMKM Kelola Stok"` (baris kecil, terpisah) —
     terkonfirmasi.
   - `"Model Terbaik"` tak ada lagi di sidebar — terkonfirmasi.
   - Label `"Rentang Waktu"` (bukan "Horizon") — terkonfirmasi.
   - Hover grafik 2 titik berbeda: `"Rab 29 Okt"` dan `"Min 05 Okt · Terjual: 126 cup"` —
     nama hari (Rabu/Rab, Minggu/Min) & bulan (Okt) Bahasa Indonesia, dua hari & bulan yang
     tervalidasi lewat hover langsung.
   - Sumbu-x grafik: format numerik (`01/11`, `01/12`, `01/01`) — tak ada nama bulan Inggris.
3. **Perkiraan Penjualan**:
   - Dropdown `"Rentang Waktu Prediksi"` (bukan "Horizon perkiraan") — terkonfirmasi.
   - Diuji rentang **30 hari** (bukan cuma 7): tabel Rincian per Hari SEMUA baris Bahasa
     Indonesia — dicek awal (`Kamis, 01 Jan`, `Jumat, 02 Jan`, `Sabtu, 03 Jan`, `Minggu, 04
     Jan`, `Senin, 05 Jan`, `Selasa, 06 Jan`) dan akhir tabel (`Rabu, 28 Jan`, `Kamis, 29 Jan`,
     `Jumat, 30 Jan`) — konsisten Indonesia di seluruh 30 baris, bukan cuma sampel.
   - Sumbu-x grafik 30 hari juga numerik (`05/10` s.d. `25/01`).
4. **Stok & Pembelian**: expander "Lihat perkiraan pemakaian bahan baku 7 hari ke depan" —
   index tabel `"Kam 01 Jan"`, `"Jum 02 Jan"`, `"Sab 03 Jan"`, `"Min 04 Jan"`, `"Sen 05 Jan"`,
   `"Sel 06 Jan"`, `"Rab 07 Jan"` — semua singkatan hari Indonesia, terkonfirmasi.
5. **Manajemen & Pengaturan → tab Resep**: judul `"Resep / Daftar Kebutuhan Bahan"` tampil
   benar (bukan "Bill of Materials") — terkonfirmasi.

### Catatan jujur soal pengujian lompatan bulan (poin 6 instruksi)

Diuji 30 hari sesuai instruksi. Forecast 30 hari dimulai 1 Januari (mengikuti titik akhir
dataset historis tetap, 31 Desember 2025 — konsisten dengan desain reset operasional T-1) dan
berakhir 30 Januari — **seluruhnya di bulan yang sama, TIDAK melewati pergantian bulan** dalam
satu tabel (Januari punya 31 hari, jadi 30 hari dari tanggal 1 tak pernah nyampai Februari).
Ini bukan bug, murni konsekuensi titik awal dataset yang fixed.

Meski begitu, mapping nama BULAN tetap tervalidasi lewat mekanisme yang PERSIS SAMA
(`ui.tanggal_id()`, satu fungsi dipakai di semua lokasi): hover grafik riwayat menunjukkan
`"Okt"` (Oktober) sedangkan tabel forecast menunjukkan `"Jan"` (Januari) — dua bulan berbeda,
dua indeks array `_BULAN_ID` berbeda, sama-sama benar. Grafik itu sendiri (garis riwayat +
perkiraan dalam satu chart, satu fungsi hover) merentang Oktober–Januari (melewati
November & Desember di titik-titik lain yang tak di-hover satu per satu, tapi memakai
fungsi identik). Tak ada indikasi index bulan manapun salah peta, tapi secara ketat: TIDAK
ada satu tabel/tampilan tunggal yang secara visual menunjukkan angka tanggal melompat
langsung dari akhir satu bulan ke awal bulan berikutnya dalam sesi pengujian ini.

## Kesimpulan

Semua 6 perubahan yang diminta + 1 temuan tak terduga (kebocoran locale tanggal Inggris)
terverifikasi lewat pengujian UI langsung di semua 4 halaman. Server dimatikan bersih
setelah pengujian.
