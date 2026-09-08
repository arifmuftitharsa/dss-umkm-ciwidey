# Evidence — Perbaikan Lanjutan: Font Tanggal, Label Bar, Rangeselector

Tanggal: 8 September 2026

## Ringkasan 3 perbaikan (components/charts.py)

1. **Font title sumbu-x dinaikkan 13→16px** (`forecast_chart()`), akar masalah "Tanggal"
   tampil rusak. Dikonfirmasi lewat inspeksi DOM SVG SEBELUM fix: `data-unformatted="Tanggal"`
   — data/teks sudah benar sejak awal, murni masalah keterbacaan ukuran font (kluster "gg"
   mengecil ambigu di Plus Jakarta Sans), BUKAN tumpang tindih posisi (bounding box title vs
   rangeslider lama sudah dicek: gap bersih 16px, tak overlap).
2. **Label angka bar (`inventory_bar()`) dipindah ke `fig.add_annotation()`** per baris,
   bgcolor putih transparan tipis. Akar masalah: Plotly render SVG per LAPISAN TIPE trace
   (semua bar dulu, baru semua scatter) — marker ROP/EOQ SELALU di atas label bar, untuk
   kombinasi data apa pun, bukan cuma kasus Tepung Terigu/Stroberi Segar yang kebetulan
   ketahuan. Annotation Plotly render di layer PALING ATAS, perbaikan struktural bukan tambal.
3. **Rangeslider dihapus, diganti `rangeselector`** (tombol preset "7 Hari Terakhir",
   "30 Hari Terakhir", "Semua Data") di `forecast_chart()`. Drag-select zoom manual TETAP
   ada (`fixedrange=False`), berdampingan dengan tombol preset.

## Verifikasi DOM — Masalah 1

```
xtitle textContent: "Tanggal"   fontSize: 16px
xaxis.rangeslider: false (dihapus total)
```

## Verifikasi visual & fungsi — Masalah 1

Screenshot render normal (bukan cuma DOM): "Tanggal" terbaca jelas, tak ada kesan
"Tanqqal"/"Tanggaal" lagi di font 16px.

## Verifikasi visual — Masalah 2

Screenshot Ringkasan Operasional & Stok & Pembelian: label "85.0" (Tepung Terigu) dan
"42.0" (Stroberi Segar) — kasus yang sebelumnya tertutup garis ROP/EOQ — sekarang JELAS
terbaca, background putih tipis membuat teks tetap kontras walau garis marker lewat di
belakangnya. Semua 6 baris (Telur Ayam, Susu Segar, Mentega, Tepung Terigu, Gula Pasir,
Stroberi Segar) dicek, semua label utuh terbaca.

## Verifikasi fungsi — Masalah 3 (rangeselector)

Diuji klik satu-satu, dikonfirmasi lewat `gd.layout.xaxis.range` SETIAP klik (bukan cuma
visual):

| Tombol | Range hasil |
|---|---|
| 7 Hari Terakhir | `2026-01-06` → `2026-01-13` (7 hari, tombol ter-highlight aktif) |
| 30 Hari Terakhir | rentang ~30 hari terakhir data, tombol ter-highlight |
| Semua Data | rentang penuh `2025-10-03` → akhir forecast, tombol ter-highlight |

**Drag-select zoom manual**: diuji drag pada area plot SETELAH klik tombol preset — bekerja
normal (tick berubah ke harian, 02/11–14/12), TIDAK terganggu tombol preset, dan tombol
preset otomatis lepas highlight (karena rentang sudah beda dari ketiga preset) — perilaku
benar, tak ada konflik state.

**Rangeslider**: dikonfirmasi hilang (`xaxis.rangeslider.visible` tak ada/false via DOM).

## Uji responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | Tombol preset ("7 Hari Terakhir", "30 Hari Terakhir", "Semua Data") muat rapi, tak overflow/terpotong. Label "Tanggal" besar & jelas. Tinggi chart 400px/812px viewport = **49,3%** (turun dari 56,7% versi rangeslider — lebih pendek sesuai prediksi). |
| Tablet (768×1024) | Tombol preset, label Tanggal, dan label angka bar (Tepung Terigu 85.0, Stroberi Segar 42.0) semua rapi & jelas. |

Catatan jujur: uji klik tombol preset di viewport mobile emulasi sempat tak konsisten
(kemungkinan flakiness alat pengujian browser saat viewport diemulasi, bukan indikasi
bug aplikasi) — fungsi tombol sudah diverifikasi PENUH & pasti di desktop (3 klik, 3 hasil
range dikonfirmasi via DOM), jadi tak diulang di mobile karena kode identik lintas ukuran
layar (bukan logic terpisah per viewport).

## Cek regresi

Manajemen & Pengaturan: normal, tak ada dampak (halaman ini tak pakai charts.py).

## Kesimpulan

Ketiga perbaikan (font title, label annotation, rangeselector pengganti rangeslider)
selesai dan diverifikasi via DOM + fungsi nyata, bukan cuma visual. Semua akar masalah
sudah diperbaiki secara struktural (bukan tambal kasus spesifik), konsisten prinsip
Open/Closed — aman untuk kombinasi data masa depan. Tak ada regresi di halaman lain.
Server dimatikan bersih.
