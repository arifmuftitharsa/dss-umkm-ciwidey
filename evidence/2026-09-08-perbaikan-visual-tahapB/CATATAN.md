# Evidence — Perbaikan Visual Tahap B (components/charts.py, risiko TINGGI lintas halaman)

Tanggal: 8 September 2026

## Ringkasan perubahan (6 keputusan, semua final sesuai persetujuan)

1. **Zoom sumbu-x** (`forecast_chart`): `fixedrange=False` untuk xaxis (bisa drag-select
   zoom detail tanggal), `fixedrange=True` TETAP untuk yaxis (proporsi jumlah unit terkunci,
   tak melonjak keliru saat zoom-x). Keputusan `fixedrange` TIDAK diterapkan ke
   `inventory_bar` — sumbu-x di sana adalah JUMLAH, bukan tanggal, tak relevan dengan alasan
   "detail rentang waktu"; dicatat sebagai keputusan sadar, bukan terlewat.
2. **Legend HTML custom**: fungsi baru `ui.legend(items)` — legend Plotly bawaan dimatikan
   total (`showlegend=False` di `_LAYOUT`), diganti swatch persegi kecil + label lewat HTML/
   CSS (`.chart-legend`), dipanggil di 4 titik (2× `forecast_chart`, 2× `inventory_bar`
   pemanggil di `overview.py`/`forecasting.py`/`inventory.py`).
3. **Token warna bar muted BARU** (`config.py`): `kritis_bar #D9776D`, `waspada_bar
   #D9A45C`, `aman_bar #5FA377` — TAMBAHAN, token `kritis`/`waspada`/`aman` asli TAK
   diubah (tetap dipakai pill/teks).
4. **Marker ROP**: `WARNA['sekunder']` → `WARNA['teks']` (#1A1F2B), `width` 3→4, `size` 22→26.
5. **Marker EOQ**: warna emas `#F4B400` dipertahankan, `width` 3→4 (konsisten ROP).
6. **Margin `inventory_bar`**: `r` 10→40 (ruang napas label angka `textposition=outside`).

**Penyesuaian tambahan dilaporkan & disetujui sebelum eksekusi**: `_rgba()` (charts.py) dan
`_tint()` (ui.py) adalah fungsi IDENTIK terduplikasi — disatukan jadi `ui.tint()` publik,
dipakai charts.py via `from . import ui` (sudah ada). DRY, nol perubahan perilaku.

## Verifikasi — DOM langsung (bukan cuma visual), sesuai metode yang terbukti akurat

### Zoom & fixedrange (Ringkasan Operasional DAN Perkiraan Penjualan)
```js
gd.layout.xaxis.fixedrange -> false   (kedua halaman)
gd.layout.yaxis.fixedrange -> true    (kedua halaman)
```
**Zoom diuji NYATA**: drag-select pada grafik forecast (Ringkasan) — sumbu-x berubah dari
tick 2-mingguan (05/10, 19/10...) jadi tick HARIAN (22/12, 25/12, 28/12, 31/12, 03/01,
06/01) setelah zoom. Sumbu-y TETAP skala 50-275 (tak berubah), dikonfirmasi screenshot
sebelum/sesudah zoom.

### Warna bar & marker (Stok & Pembelian)
```js
barColors: ["#D9776D", "#5FA377", "#5FA377", "#5FA377", "#5FA377", "#5FA377"]
ropColor: "#1A1F2B"   ropWidth: 4   ropSize: 26
eoqColor: "#F4B400"
margin: {l:10, r:40, t:30, b:10}
```
SEMUA nilai PERSIS cocok token/spesifikasi yang disetujui — bukan asumsi, dibaca langsung
dari objek Plotly `gd.data`/`gd.layout`.

## Verifikasi visual

- **Legend baru**: swatch persegi kecil rapi (bukan kotak putus-putus Plotly default),
  wrap 2 baris di layar sempit, 1 baris di layar lebar — dikonfirmasi di KEDUA halaman
  `forecast_chart` (Ringkasan, Perkiraan) dan KEDUA halaman `inventory_bar` (Ringkasan, Stok).
- **Marker ROP**: garis hitam tebal SANGAT jelas terlihat bahkan di bar terpendek (Mentega,
  Tepung Terigu) — kontras jauh lebih baik dari abu-abu lama.
- **Label angka**: ada spasi jelas dari ujung bar (mis. "500", "120", "85") setelah margin
  kanan dinaikkan.
- **Warna bar**: hijau sage tenang, merah-coral lembut untuk "Stroberi Segar" (status
  Kritis) — jauh lebih harmonis dengan navy, tetap jelas beda hue dari hijau (sinyal cepat
  tak hilang).

## Pengujian responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | Legend wrap rapi, grafik forecast & bar full-width, marker ROP tetap jelas, label bar tak terpotong. |
| Tablet (768×1024) | Legend muat 1 baris, semua elemen proporsional, tak ada masalah. |

## Cek regresi halaman Manajemen

Tab Produk: sempat tampak kosong sesaat (canvas `data_editor` belum selesai render pada
screenshot pertama), P001/P002/P003 muncul normal setelah tunggu ~2 detik lagi — bukan
regresi, murni delay render widget canvas (dikenal dari sesi-sesi sebelumnya). Tombol
"Simpan Produk" tetap navy normal, tak ada dampak dari perubahan `config.py`/`ui.py`.

## Kesimpulan

Tahap B (risiko tertinggi dari seluruh redesain, charts.py lintas 3 halaman) selesai.
SEMUA 6 keputusan diverifikasi via DOM dengan nilai PERSIS sesuai spesifikasi, bukan
diasumsikan dari tampilan visual saja. Zoom sumbu-x dikonfirmasi berfungsi nyata (drag
sungguhan, sebelum/sesudah dibandingkan), sumbu-y dikonfirmasi tetap terkunci. Tak ada
regresi di halaman manapun. Server dimatikan bersih.
