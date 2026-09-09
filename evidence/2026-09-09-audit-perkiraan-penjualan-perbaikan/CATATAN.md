# Evidence — Perbaikan 4 Temuan Audit Perkiraan Penjualan

Tanggal: 9 September 2026

## Ringkasan 4 perbaikan (`app/views/forecasting.py`)

1. **Legend dinamis** — `"Perkiraan 7 hari"` hardcode → `f"Perkiraan {horizon} hari"`.
2. **Kartu aksi netral horizon** — "...minggu ini" → f"...dalam {horizon} hari ke depan".
   Dicek, tak ada penyebutan "minggu"/rentang waktu implisit lain di teks kartu ini.
3. **Subtext section grafik** — diisi "Riwayat penjualan dan perkiraan ke depan."
4. **`round()` menggantikan `int()` (truncate)** — diseragamkan di KPI (total, rata-rata)
   DAN kolom tabel "Perkiraan terjual" — keputusan: kalau cuma salah satu dibulatkan,
   total KPI bisa tak cocok dengan sum baris tabel (inkonsistensi baru).

## Temuan 4 — bukti konkret sebelum vs sesudah

Dihitung langsung dari data forecast real (P001, sebelum ada perubahan kode berjalan):

| Horizon | Rata-rata mentah | `int()` (lama) | `round()` (baru) |
|---|---|---|---|
| 7 | 69.43 | 69 | 69 (sama, kebetulan) |
| **14** | **58.71** | **58** | **59** ← BEDA NYATA |
| 30 | 59.1 | 59 | 59 (sama, kebetulan) |

Horizon 14 membuktikan perbedaan nyata (58.71 → truncate ke 58 vs round ke 59) — bukan
kebetulan sama. Dikonfirmasi di UI: KPI "Rata-rata per Hari" horizon 14 tampil **59 jar**
(sebelumnya, dengan kode lama, akan tampil 58).

## Verifikasi legend dinamis — 3 horizon

| Horizon dipilih | Legend tampil | Screenshot |
|---|---|---|
| 7 hari | "Perkiraan 7 hari" | dikonfirmasi |
| 14 hari | "Perkiraan 14 hari" | dikonfirmasi |
| 30 hari | "Perkiraan 30 hari" | dikonfirmasi |

## Verifikasi kartu aksi

| Horizon | Teks kartu (sebelum → sesudah) |
|---|---|
| 14 hari | "...minggu ini" → **"...dalam 14 hari ke depan"** |
| 30 hari | "...minggu ini" → **"...dalam 30 hari ke depan"** |

Kedua kasus dikonfirmasi screenshot — tak ada lagi kesalahan konteks waktu.

## Verifikasi subtext

"Grafik Perkiraan Produk [nama] — Riwayat penjualan dan perkiraan ke depan." muncul
konsisten di desktop, tablet, mobile.

## Cek regresi — Ringkasan Operasional

Halaman ini JUGA pakai `charts.forecast_chart()` dan `ui.legend()`, tapi legend-nya
di-hardcode TERPISAH di `overview.py` (bukan diedit sesi ini) dan selalu pakai horizon
default (7 hari) — dikonfirmasi masih tampil "Perkiraan 7 hari" dengan benar, TAK
terpengaruh perubahan di `forecasting.py`. Bar chart "Kondisi Stok Bahan Baku" (label
angka bulat dari perbaikan sesi lalu) juga tetap normal.

## Uji responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375px) | Subtext, legend, KPI semua rapi, tak ada elemen tabrakan/terpotong. |
| Tablet (768px) | Sama rapi. |

## Kesimpulan

Keempat temuan diperbaiki dan diverifikasi dengan bukti konkret — termasuk kasus nyata
(horizon 14, rata-rata 58.71) yang membuktikan `round()` vs `int()` benar-benar
menghasilkan angka berbeda, bukan kebetulan sama. Tak ada regresi di Ringkasan
Operasional (memakai komponen sama tapi jalur kode terpisah). Server dimatikan bersih.
