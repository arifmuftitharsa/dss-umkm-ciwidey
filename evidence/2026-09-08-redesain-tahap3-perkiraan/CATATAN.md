# Evidence — Redesain Tahap 3: Halaman Perkiraan Penjualan

Tanggal pengujian: 8 September 2026

## Ringkasan perubahan

`views/forecasting.py` sebagian sudah tersentuh sesi sebelumnya (em dash judul section
`forecasting.py:63`, deskripsi warna grafik) — sesi ini audit MENYELURUH sesuai pola
Tahap 2. Halaman ini juga tak punya HTML/CSS custom sendiri, semua kartu lewat komponen
`ui.py` yang sudah diredesain Tahap 1.

**Temuan utama (baru, belum ditemukan sesi sebelumnya):** fungsi `alasan()` (kolom
"Catatan" tabel Rincian per Hari) — 3 dari 5 kemungkinan nilai pakai em dash:
`"Hari libur — ramai"`, `"Akhir pekan — ramai"`, `"Hujan — cenderung sepi"`. Ini isi DATA
yang dirender berulang tiap baris tabel (bisa 7-30 baris tergantung rentang), bukan cuma
label statis — signifikan karena berulang.

**Perbaikan:** ganti em dash jadi koma di ketiga nilai (`"Hari libur, ramai"`,
`"Akhir pekan, ramai"`, `"Hujan, cenderung sepi"`). 2 nilai lain (`"Sekitar hari libur"`,
`"Hari biasa"`) sudah tanpa dash, tak diubah.

## Audit lain (tak ada masalah)

- ALL-CAPS/text-transform inline: TIDAK ADA.
- Hex hardcoded: TIDAK ADA (warna chart sudah dari `charts.py`, token Tahap 1-2).
- Override CSS lokal: TIDAK ADA.
- Tabel Rincian per Hari: `st.dataframe()` native, otomatis ikut `.stDataFrame` CSS global
  dari Tahap 1 — tak butuh kode tambahan.

## Verifikasi checklist fitur

Dropdown pilih produk, dropdown rentang waktu, peringatan kondisional, 2 KPI, grafik
forecast, tabel Rincian per Hari, kartu aksi kondisional — SEMUA ADA, tak ada yang hilang.

## Pengujian interaksi

- **Dropdown rentang waktu**: diuji ganti 7 → 30 hari — total/rata-rata KPI ter-update
  benar (1773 jar/59 jar), peringatan kondisional (>16 hari) muncul dengan styling
  `st.warning()` native (otomatis ikut tema Tahap 1, tak perlu kode tambahan).
- **Dropdown pilih produk**: diuji ganti Selai Stroberi → Strawberry Cake — KPI, satuan
  (loyang), dan grafik ter-update benar (660 loyang/22 loyang), interaksi normal.

## Verifikasi kolom "Catatan" (SEMUA varian, bukan cuma satu baris)

Dicek di rentang 30 hari (Selai Stroberi) — 4 dari 5 varian TERKONFIRMASI VISUAL bersih
tanpa dash:
- `"Hari libur, ramai"` ✓
- `"Sekitar hari libur"` ✓ (tak berubah, sudah bersih)
- `"Akhir pekan, ramai"` ✓
- `"Hari biasa"` ✓ (tak berubah, sudah bersih)

**Catatan jujur:** varian `"Hujan, cenderung sepi"` TIDAK muncul secara alami di window
data 30 hari yang diuji (kondisi `rainfall_mm > 20` kebetulan tak terpenuhi hari manapun
dalam rentang ini, dataset sintetis deterministik). Tidak diverifikasi visual langsung —
tapi perubahan kodenya pola identik dengan 2 varian lain yang sudah dikonfirmasi (return
string sederhana, sudah lolos syntax check), risiko regresi sangat rendah.

## Pengujian responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | Dropdown full-width, 2 KPI ditumpuk vertikal border-kiri, judul section 2 baris tanpa dash. Tabel Rincian per Hari (3 kolom) **MUAT PENUH TANPA SCROLL HORIZONTAL** — Streamlit dataframe otomatis menyusutkan lebar kolom proporsional, tak ada teks terpotong, semua baris terbaca jelas. Tak perlu CSS tambahan untuk scroll horizontal (dugaan awal di analisis Tahap 1 soal tabel banyak kolom TIDAK terjadi di sini, cuma 3 kolom). |
| Tablet (768×1024) | 2 KPI sejajar, dropdown sejajar, grafik & tabel utuh. |

## Cek regresi halaman lain

Ringkasan Operasional, Stok & Pembelian, Manajemen & Pengaturan — dicek screenshot cepat,
SEMUA tampil normal, tak ada regresi dari perubahan `forecasting.py`.

## Kesimpulan

Tahap 3 (halaman Perkiraan Penjualan) selesai. 1 temuan signifikan (em dash berulang di
data tabel) ditemukan dan diperbaiki. Tak ada fitur hilang, interaksi dropdown berfungsi
normal, tabel responsif tanpa perlu kode tambahan. Server dimatikan bersih.
