# Evidence — Redesain Tahap 2: Halaman Ringkasan Operasional

Tanggal pengujian: 8 September 2026

## Ringkasan perubahan

`views/overview.py` tak punya HTML/CSS custom sendiri (semua kartu lewat `ui.kpi()`/
`ui.section()`/`ui.action()` yang sudah diredesain Tahap 1) — cek awal (langkah 1-2)
mengonfirmasi tak ada override CSS lokal yang bentrok. Perbaikan Tahap 2 murni teks + 1
bug warna lintas halaman:

1. `overview.py:21` — titik-tengah "· pantauan minggu ini" dihapus, jadi koma.
2. `overview.py:66` — em dash di judul section "Perkiraan Penjualan — {nama}" dihapus,
   diganti struktur kalimat "Perkiraan Penjualan Produk {nama}".
3. `overview.py:93` — em dash di isi kartu aksi dihapus, diganti koma.
4. `components/charts.py` — bug sisa Tahap 1: `rgba(14,138,107,...)` (hijau lama, diketik
   manual bukan referensi token) di trace "Rentang perkiraan" `forecast_chart()`, terlewat
   saat token diganti navy. Diperbaiki dengan helper `_rgba(hex, alpha)` yang menghitung
   rgba dari `WARNA['primer']` langsung — dijamin ikut kalau token berubah lagi nanti, tak
   ada hardcode ulang. TANPA ubah signature fungsi.

## Temuan TAMBAHAN (dilaporkan, TIDAK dieksekusi — di luar 4 item yang disetujui)

- `STUDI_KASUS["nama"]` di `config.py` = `"UMKM Olahan Stroberi — Desa Wisata Alamendah"` —
  mengandung em dash bawaan DATA (bukan format teks di `overview.py`), tampil di judul
  halaman ini. Di luar scope 4 item yang disetujui sesi ini (itu ubah data config, dipakai
  kemungkinan di tempat lain juga) — dicatat untuk keputusan terpisah.
- Teks deskripsi grafik "Garis biru = penjualan 60 hari lalu, garis hijau = perkiraan 7
  hari, area hijau muda = rentang kemungkinan" (`overview.py:67-69`) sudah TAK AKURAT --
  warna chart sekarang navy/slate, bukan biru/hijau lagi (sejak Tahap 1). Bukan bagian 4
  item yang disetujui, TIDAK diubah sekarang -- dicatat untuk Tahap 2 lanjutan atau sesi
  terpisah.

## Verifikasi checklist fitur (halaman Ringkasan Operasional)

3 KPI (Perkiraan Penjualan, Bahan Perlu Dibeli, Hari Libur Nasional), grafik forecast
produk volume tertinggi, panel "Yang Perlu Dilakukan" (kartu aksi), grafik bar kondisi
stok — SEMUA ADA, tak ada yang hilang.

## Verifikasi visual

- Subjudul: "UMKM Olahan Stroberi — Desa Wisata Alamendah, pantauan minggu ini (7 hari ke
  depan)" — titik-tengah hilang (koma), em dash SISA cuma dari `STUDI_KASUS["nama"]` (temuan
  di atas, di luar scope).
- Judul section: "Perkiraan Penjualan Produk Jus Stroberi Segar" — tanpa dash, natural.
- Kartu aksi "Perkiraan lonjakan penjualan minggu ini": "...Penjualan cenderung naik,
  siapkan stok lebih banyak." — koma, tanpa dash.
- KPI card: border-kiri navy, tanpa shadow — konsisten Tahap 1 (tak ada override lokal di
  file ini, dikonfirmasi kosong).

## Verifikasi warna pita keyakinan (lintas 2 halaman, bukti DOM langsung)

Dicek lewat `document.querySelectorAll('path.js-fill')` (bukan cuma visual screenshot):

- **Ringkasan Operasional**: `fill: rgb(30, 58, 95); fill-opacity: 0.2` — `#1E3A5F` navy,
  BUKAN hijau lama.
- **Perkiraan Penjualan** (halaman lain, dipakai `forecast_chart()` yang sama): `fill:
  rgb(30, 58, 95); fill-opacity: 0.2` — IDENTIK, konfirmasi perbaikan konsisten lintas
  halaman, bukan cuma satu tempat.

## Pengujian responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | KPI ditumpuk vertikal, teks baru tampil natural tanpa tanda pisah, judul section 2 baris terbaca jelas. |
| Tablet (768×1024) | 3 KPI sejajar, action card & grafik utuh, tak ada elemen terpotong. |

## Cek regresi halaman lain

- **Stok & Pembelian**: KPI border-kiri, action card, tabel — tampil normal, tak ada
  regresi dari perubahan `charts.py`.
- **Manajemen & Pengaturan**: tab Produk, tombol "Simpan Produk" (navy), tabel data_editor
  — tampil normal, tak ada regresi.

## Kesimpulan

4 perbaikan Tahap 2 (3 teks + 1 bug warna lintas halaman) selesai dan terverifikasi. Tak
ada fitur hilang, tak ada regresi di halaman lain. Server dimatikan bersih. 2 temuan
tambahan (em dash data `STUDI_KASUS`, deskripsi warna grafik usang) dicatat untuk keputusan
terpisah, tidak dieksekusi sesi ini.

---

## Susulan — perbaikan 2 temuan yang ditunda + 1 temuan baru

Dikerjakan sesi sama, sebelum commit, sesuai approval susulan.

### Temuan 1 — deskripsi warna usang (sekarang diperbaiki)

Warna chart berubah sejak Tahap 1 (navy/slate), tapi teks deskripsi di 3 lokasi masih
menyebut warna lama:

| Lokasi | Sebelum | Sesudah |
|---|---|---|
| `overview.py:67-69` | "Garis biru = penjualan..., garis hijau = perkiraan..., area hijau muda" | "Garis abu-abu = penjualan..., garis biru tua = perkiraan..., area biru muda" |
| `forecasting.py:64` | "Garis hijau = perkiraan" | "Garis biru tua = perkiraan" |
| `inventory.py:72` | "Garis biru = batas aman (ROP) · garis kuning = EOQ" | "Garis abu-abu = batas aman (ROP), garis kuning = EOQ" — titik-tengah SEKALIAN dihapus karena baris yang sama persis sedang diedit untuk alasan warna, bukan scope baru terpisah |

Warna EOQ (`#F4B400`, "kuning") tak diubah — sudah akurat sejak awal, tak tersentuh Tahap 1.

### Temuan 2 — em dash `STUDI_KASUS["nama"]` (sekarang diperbaiki)

`config.py`: `"UMKM Olahan Stroberi — Desa Wisata Alamendah"` → `"UMKM Olahan Stroberi,
Desa Wisata Alamendah"`. Dicek dulu: kunci `"nama"` HANYA dipakai satu tempat di seluruh
`app/` (`overview.py:21`), sudah dibungkus koma di sekitarnya sejak perbaikan Tahap 2 —
aman diubah tanpa merusak format kalimat gabungan. Kunci lain (`lokasi`, `koordinat`,
`horizon_hari`) tak tersentuh, dipakai di `app.py`/`core/forecasting.py`/`data/weather.py`
tanpa masalah dash.

### Temuan baru (ditemukan saat review, disetujui & diperbaiki sekalian)

`forecasting.py:63` — `ui.section(f"Grafik Perkiraan — {nama}", ...)` masih em dash, pola
sama dengan `overview.py:66` yang sudah diperbaiki Tahap 2. Diganti
`f"Grafik Perkiraan Produk {nama}"`.

### Pengujian susulan

`streamlit run app.py`, buka Perkiraan Penjualan: judul section
**"Grafik Perkiraan Produk Selai Stroberi"** — tanpa dash, natural. Deskripsi **"Garis biru
tua = perkiraan; area terang = rentang kemungkinan"** — akurat dengan warna aktual. Server
dimatikan bersih setelah pengujian.

### Kesimpulan susulan

Kedua temuan yang ditunda + 1 temuan baru (em dash `forecasting.py:63`) sudah diperbaiki
dan diverifikasi. Total perubahan sesi ini (Tahap 2 + susulan): `config.py`,
`views/overview.py`, `views/forecasting.py`, `views/inventory.py`, `components/charts.py`.
