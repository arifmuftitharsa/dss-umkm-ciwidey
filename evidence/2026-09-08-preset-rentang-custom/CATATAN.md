# Evidence — Ganti Rangeselector Plotly dengan Tombol Custom + Perbaikan Bug Rentang

Tanggal: 8 September 2026

## Akar bug "7 Hari Terakhir" rusak (rangeselector Plotly lama)

Dikonfirmasi via DOM SEBELUM perbaikan: klik tombol Plotly `rangeselector` "7 Hari
Terakhir" menghasilkan `xaxis.range = [2026-01-06, 2026-01-13]`, padahal data forecast
terakhir cuma sampai `2026-01-07`. `stepmode="backward"` Plotly menghitung dari batas
ATAS axis yang sudah di-*pad* otomatis (bukan tanggal data terakhir sungguhan) — 6 dari
7 hari window itu KOSONG, itu sebabnya grafik tampak "garis datar rusak".

## Solusi

Rangeselector Plotly dihapus total dari `components/charts.py`. Diganti tombol Streamlit
custom (`ui.rentang_riwayat_buttons()`, fungsi shared baru di `components/ui.py`) yang
MEMFILTER DATA DI PYTHON (`ui.filter_riwayat_hari()`) sebelum dikirim ke
`forecast_chart()` — chart terima data yang sudah tepat, tak ada perhitungan rentang
diserahkan ke Plotly lagi. Dipanggil dari `views/overview.py` dan `views/forecasting.py`,
session_state terpisah per halaman (`rentang_chart_ringkasan` / `rentang_chart_perkiraan`).

## Verifikasi fungsi — bug lama dikonfirmasi HILANG

| Tombol | Hasil (Ringkasan) | Hasil (Perkiraan) |
|---|---|---|
| 7 Hari Terakhir | Data terisi utuh 25/12–06/01 (8 titik riwayat + 7 titik forecast), TIDAK ada garis datar/kosong | Data terisi utuh 24/12–07/01, sama baiknya |
| 30 Hari Terakhir | Data terisi utuh 07/12–04/01 | — |
| Semua Data | Rentang penuh 03/10–13/01 | Rentang penuh, default |

Dikonfirmasi via DOM (`gd.data[...].x.length`, bukan cuma visual): `futPoints: 7`
(forecast SELALU utuh, tak pernah difilter, sesuai keputusan), `histPoints: 8` (riwayat
terpotong sesuai preset).

## Verifikasi tombol aktif/tidak aktif

Tombol yang sedang dipilih render `type="primary"` (navy solid) — sisanya
`type="secondary"` (outline) — dikonfirmasi screenshot di ketiga preset, berpindah
dengan benar tiap klik.

## Verifikasi isolasi state antar halaman

Set "7 Hari Terakhir" di Perkiraan Penjualan, lalu pindah ke Ringkasan Operasional:
Ringkasan TETAP di "Semua Data" (state sebelumnya, tak tertular) — dikonfirmasi
`gd.layout.xaxis.range` = rentang penuh (`2025-10-03` s.d. `2026-01-13`), BUKAN 7 hari.
Session state per halaman terbukti benar-benar terpisah.

## Verifikasi drag-select zoom manual

Diuji drag pada area plot setelah klik preset "Semua Data" — bekerja normal (tick
berubah ke harian, 26/10–07/12), tak terganggu tombol baru.

## Uji responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | 3 tombol stack vertikal penuh-lebar (perilaku bawaan `st.columns` Streamlit di layar sempit), teks utuh tak terpotong. Tinggi chart 380px/812px = **46,8%** (kembali ke proporsi awal — tak ada lagi rangeslider/rangeselector Plotly yang menambah tinggi). |
| Tablet (768×1024) | 3 tombol muat 1 baris rapi, label bar tak tertutup (masih dari perbaikan sebelumnya), semua utuh. |

## Cek regresi

Stok & Pembelian, Manajemen & Pengaturan: normal, tak ada dampak.

## Kesimpulan

Bug rentang "7 Hari Terakhir" yang salah hitung sudah diperbaiki di AKAR MASALAHNYA
(pindah filter dari Plotly ke Python, bukan menambal parameter Plotly) — dikonfirmasi
lewat pengujian nyata (klik + DOM), bukan asumsi. Tombol custom menyatu dengan token
desain (primary/secondary Streamlit, konsisten pola active-state di aplikasi). State
per halaman terbukti terisolasi. Tak ada regresi. Server dimatikan bersih.
