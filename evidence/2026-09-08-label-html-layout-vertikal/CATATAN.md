# Evidence — Label "Tanggal" HTML, Layout Vertikal Ringkasan, Caption Baru

Tanggal: 8 September 2026

## Ringkasan 3 perbaikan

1. **Label "Tanggal" kembali**, tapi via HTML (`ui.label_sumbu_tanggal()`), BUKAN
   `xaxis_title` Plotly (SVG) — menghindari akar bug DPR (commit `21803e8`) sepenuhnya
   karena render browser native tak lewat jalur SVG yang rentan. Rata tengah, di bawah
   blok chart+rangeslider (posisi paling dekat dicapai dengan "di bawah grafik" karena
   rangeslider baked-in satu render Plotly, tak bisa disisip di antaranya — kendala
   teknis dijelaskan & disetujui di analisis sebelum eksekusi).
2. **Caption diganti** teks lebih natural: "↔ Bisa digeser untuk lihat rentang tanggal
   lain" (dari 3 opsi, Opsi 2 dipilih). Margin negatif (`-.5rem`, sumber tabrakan
   layout) diganti margin positif konsisten (`.25rem`) di kedua elemen baru.
3. **`overview.py`**: struktur `st.columns([1.55, 1])` (grafik|aksi berdampingan)
   dihapus, diganti susunan vertikal — "Yang Perlu Dilakukan" (isi TAK diubah) di ATAS
   full-width, grafik forecast di BAWAH full-width. `forecasting.py` TAK disentuh
   struktur layoutnya (dikonfirmasi tak punya pola berdampingan sejak awal).

## Verifikasi urutan & spacing — Ringkasan Operasional

Screenshot: KPI cards → **"Yang Perlu Dilakukan"** (full-width, di atas) → grafik
forecast (full-width) → label **"Tanggal"** (rata tengah) → caption **"↔ Bisa digeser
untuk lihat rentang tanggal lain"** (rata kiri) → "Kondisi Stok Bahan Baku". Tak ada
tabrakan/overlap antar elemen — spacing konsisten kecil di seluruh urutan baru.

## Verifikasi label bebas bug DPR

```js
hasSvgTitle: false   // .xtitle Plotly tak ada sama sekali
```
Label "Tanggal" murni elemen `<div>` HTML — screenshot visual bersih, tak ada kesan
"Tanqqal"/rusak di manapun (desktop, tablet, mobile).

## Verifikasi fungsi — rangeslider & drag-select zoom

| Aksi | Hasil |
|---|---|
| Drag rangeslider (Ringkasan) | range penuh → `2025-10-03 - 2025-12-07` |
| Drag-select zoom manual (Ringkasan) | `2025-10-14 - 2025-11-10` (setelah reset autorange) |
| Drag rangeslider (Perkiraan Penjualan) — dicek visual, sama fungsinya | rangeslider tampil & responsif |

## Verifikasi Perkiraan Penjualan (tak terpengaruh Perbaikan 3)

Screenshot: grafik langsung tampil (tak ada kartu-aksi berdampingan sejak awal),
label "Tanggal" + caption baru muncul benar, identik pola dengan Ringkasan.

## Uji responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | Susunan vertikal baru: KPI → "Yang Perlu Dilakukan" → grafik → label → caption, urutan scroll natural, tak kepanjangan aneh. Tinggi chart 420/812 = 51,7% (sama seperti sebelumnya, tak berubah oleh perbaikan ini). Label+caption rapi tanpa tabrakan. |
| Tablet (768×1024) | Sama rapi, label bar `inventory_bar` (perbaikan sesi lalu) tetap utuh. |

## Cek regresi

Stok & Pembelian, Manajemen & Pengaturan: normal, tak ada dampak.

## Kesimpulan

Ketiga perbaikan selesai sesuai spesifikasi. Label "Tanggal" kembali tanpa risiko DPR
(HTML, bukan SVG). Tata letak rapi, tak ada tabrakan spacing (margin negatif dihapus).
Caption lebih natural. `overview.py` sekarang susunan vertikal (aksi dulu, baru
grafik) sesuai keputusan Arif; `forecasting.py` dikonfirmasi tak perlu perubahan
serupa. Tak ada regresi di halaman lain. Server dimatikan bersih.
