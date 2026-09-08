# Evidence — Analisis Urutan Sidebar + Perhalus Kotak Peringatan

Tanggal: 8 September 2026

## Bagian 1 — Urutan sidebar (analisis, TANPA perubahan kode struktural)

Keluhan: nav (4 menu) muncul di atas nama+tagline "UPStock", terbalik dari struktur yang
direncanakan.

**Temuan**: dicek dari dokumentasi resmi `help(st.navigation)` sebelumnya — `position="sidebar"`
SELALU render widget nav di PALING ATAS sidebar, terlepas urutan pemanggilan kode di
sekitarnya. Ini keterbatasan API Streamlit, BUKAN bug urutan kode di `app.py` (`st.navigation()`
dipanggil sebelum blok `with st.sidebar:`, tapi urutan pemanggilan itu tak menentukan
posisi render nav). Satu-satunya alternatif resmi, `position="top"`, memindah nav jadi
header horizontal di area konten utama — ganti paradigma navigasi total, di luar scope.

**Keputusan Arif**: diterima apa adanya, TANPA perubahan kode. Perbaikan HANYA komentar
`app.py` baris 56-66 — sebelumnya menyiratkan urutan render itu keputusan desain sadar,
sekarang jujur menjelaskan ini keterbatasan API yang dikonfirmasi dari dokumentasi resmi.

## Bagian 2 — Perhalus kotak peringatan Tab Catat Penjualan

**Keputusan Arif**: Opsi B — `st.warning()` (kuning) diganti `ui.action()` level `"info"`
(border-kiri navy, komponen yang sudah dipakai luas di seluruh app). Checkbox konfirmasi
dan tombol "Mulai Pakai Data Real Hari Ini" — mekanisme keamanan T-1 — **TIDAK disentuh
sama sekali**, cuma kalimat pertama teks peringatan jadi "judul" card, sisanya jadi
"detail". Makna teks lengkap dipertahankan, tak ada informasi dihilangkan.

## PROTOKOL KEAMANAN — hasil eksplisit (WAJIB)

Baseline SEBELUM testing:
```
$ git status --porcelain app/data/historis_penjualan.csv
(kosong)
$ git diff app/data/historis_penjualan.csv
(kosong)
```

Observasi Tab Catat Penjualan: **HANYA visual** — checkbox dicek TIDAK tercentang, tombol
"Mulai Pakai Data Real Hari Ini" dicek TETAP status disabled (abu-abu) — sama persis
kondisi sebelum perubahan. **TIDAK PERNAH** klik checkbox/tombol/submit apa pun.

Verifikasi SEGERA setelah observasi:
```
$ git status --porcelain app/data/historis_penjualan.csv
(kosong)
$ git diff app/data/historis_penjualan.csv
(kosong)
```

**Hasil: NOL perubahan data, dikonfirmasi baseline dan sesudah observasi — identik.**

## Verifikasi visual & fungsi

- Kotak peringatan: border-kiri navy (`.action.info`), radius 6px, TANPA warna kuning
  mencolok — teks lengkap terbaca ("Sistem masih memakai data latihan" sebagai judul,
  sisanya sebagai detail).
- Checkbox: unchecked, tombol aktivasi disabled — state SAMA PERSIS sebelum perubahan
  visual ini, dikonfirmasi visual.

## Cek regresi

Ringkasan Operasional, Perkiraan Penjualan, Stok & Pembelian — dicek screenshot, SEMUA
normal, tak ada dampak dari perubahan `app.py`/`pengaturan.py`.

## Kesimpulan

Sidebar: keterbatasan API diterima, komentar diperjujur, nol perubahan kode struktural.
Kotak peringatan: gaya visual dihaluskan (Opsi B) TANPA mengubah mekanisme keamanan T-1
sedikit pun — checkbox+tombol tetap wajib, verifikasi ganda (baseline + sesudah) konfirmasi
nol data tertulis tak sengaja. Server dimatikan bersih.
