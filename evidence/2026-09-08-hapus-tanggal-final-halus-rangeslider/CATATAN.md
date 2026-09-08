# Evidence — Hapus Label Tanggal (Final), Rangeslider Diperhalus

Tanggal: 8 September 2026

## Ringkasan 3 perbaikan

1. **`label_sumbu_tanggal()` dihapus total** dari `ui.py` (bukan cuma pemanggilannya) —
   keputusan FINAL Arif, tak diperlukan sama sekali. Panggilan dihapus dari
   `overview.py` dan `forecasting.py`.
2. **Caption `petunjuk_geser()` margin disesuaikan**: `.25rem → .5rem` — dulu jaraknya
   dihitung untuk ada elemen `label_sumbu_tanggal()` di atasnya; sekarang caption
   langsung di bawah rangeslider tanpa perantara, margin dinaikkan supaya tetap ada
   jarak wajar (tak nempel).
3. **Rangeslider diperhalus**: `borderwidth 2→1`. **Marker hari libur dikecilkan**:
   forecast `14→11`, historis `11→9` — investigasi dikonfirmasi Plotly TAK punya
   parameter ukuran marker terpisah untuk rangeslider vs grafik utama (rangeslider
   render ulang trace yang sama persis); satu-satunya cara adalah mengecilkan
   `marker.size` di sumbernya, ikut memengaruhi grafik utama (trade-off yang sudah
   disetujui sebelum eksekusi).

## Verifikasi DOM — semua nilai persis spesifikasi

```js
rsBorderwidth: 1
holMarkerSize: 11    // forecast
holHMarkerSize: 9    // historis
hasSvgTitle: false   // label Tanggal benar-benar tak ada
```

## Verifikasi visual

- Label "Tanggal" sudah tak ada sama sekali di manapun (Ringkasan, Perkiraan).
- Caption "↔ Bisa digeser untuk lihat rentang tanggal lain" punya jarak wajar dari
  rangeslider, tak nempel.
- Marker kuning (hari libur) di grafik utama TETAP jelas terlihat meski dikecilkan —
  dikonfirmasi screenshot, tak ada kesulitan visual mengenali penanda.
- Rangeslider terlihat lebih halus (border 1px vs 2px sebelumnya).

## Verifikasi fungsi — drag rangeslider & drag-select zoom

| Aksi | Hasil |
|---|---|
| Drag rangeslider (Ringkasan) | range penuh → `2025-10-03 - 2025-12-07` |
| Drag-select zoom manual (Ringkasan) | `2025-10-15 - 2025-11-10` |

**Catatan proses**: sempat berulang kali gagal drag karena viewport tab browser diam-
diam balik ke 375px (sisa emulasi test sebelumnya) — pola yang sudah beberapa kali
terjadi di sesi-sesi sebelumnya juga. Selalu diverifikasi ulang `window.innerWidth`
sebelum menyimpulkan gagal fungsi; setelah viewport dikonfirmasi benar (1280px), drag
langsung berfungsi normal.

## Uji responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | Tak ada label Tanggal, marker proporsional, caption rapi tanpa nempel rangeslider. |
| Tablet (768×1024) | Sama rapi, label bar `inventory_bar` tetap utuh (tak terdampak perubahan ini). |

## Cek regresi

Stok & Pembelian, Manajemen & Pengaturan: normal, tak ada dampak.

## Kesimpulan

Ketiga perbaikan selesai sesuai spesifikasi persis (dikonfirmasi DOM). Label Tanggal
dihapus total secara final (kode + fungsi, bukan cuma pemanggilan). Caption punya
spacing proporsional. Rangeslider lebih halus tanpa mengorbankan fungsi drag maupun
kejelasan marker hari libur di grafik utama. Tak ada regresi. Server dimatikan bersih.
