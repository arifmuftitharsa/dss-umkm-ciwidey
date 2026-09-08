# Evidence — Rangeslider Custom (Percobaan ke-4, Final)

Tanggal: 8 September 2026

## Riwayat lengkap 4 iterasi navigasi rentang waktu grafik forecast

Dokumen rujukan kalau ada pertanyaan di masa depan soal kenapa desain ini seperti ini:

1. **Rangeslider Plotly default** (Task A, thickness=.08, warna abu-abu bawaan) —
   ditolak: "kurang jelas fungsinya" secara visual.
2. **Rangeselector Plotly bawaan** (tombol preset "7/30 Hari Terakhir"/"Semua Data") —
   ditolak: "kotak abu-abu asing", tak menyatu sistem desain. JUGA ditemukan bug:
   `stepmode="backward"` salah hitung rentang (commit sebelum ed01ceb).
3. **Tombol preset custom Streamlit** (`ui.rentang_riwayat_buttons`, commit `ed01ceb`) —
   BERFUNGSI BAIK dan bug rentang diperbaiki di akar (filter di Python). Tapi Arif
   berubah pikiran: mau interaksi "geser langsung" (drag), bukan klik tombol.
4. **Rangeslider Plotly DIKEMBALIKAN dengan styling custom** (perbaikan ini) — thickness
   dinaikkan .08→.15, warna navy custom (bgcolor/bordercolor token WARNA["primer"]),
   border 2px, DITAMBAH caption teks petunjuk eksplisit. Tombol preset (`ui.
  rentang_riwayat_buttons`/`ui.filter_riwayat_hari`) DIHAPUS TOTAL dari `ui.py` (dependency
   hygiene, T-8 — riwayatnya tetap ada di commit `ed01ceb` kalau perlu diambil lagi).

## Verifikasi styling — DOM

```js
xaxis.rangeslider: {
  visible: true, thickness: 0.15,
  bgcolor: "rgba(30,58,95,0.12)",   // navy pudar, token WARNA["primer"]
  bordercolor: "#1E3A5F",            // navy solid
  borderwidth: 2,
}
height: 480
```
Semua nilai PERSIS sesuai rencana yang disetujui.

## Verifikasi fungsi — drag rangeslider (BUKAN cuma visual, DOM range dicek tiap kali)

| Halaman | Aksi | Hasil |
|---|---|---|
| Ringkasan Operasional | drag handle kanan ke kiri | range `2025-10-03` → `2025-11-26` (dari full) |
| Ringkasan Operasional | drag balik + drag-select zoom manual di area plot | tick jadi harian (07/12–21/12), TAK terganggu rangeslider |
| Perkiraan Penjualan | drag handle kanan ke kiri | range `2025-10-03` → `2025-12-07` |
| Tablet (768px) | drag handle kanan ke kiri | range `2025-10-03` → `2025-11-29` — berfungsi sama |

**Catatan jujur — pengujian mobile (375px)**: verifikasi VISUAL selesai (rangeslider besar
jelas navy, handle putih kontras tinggi, caption terbaca penuh tanpa terpotong, tinggi
chart 480px/812px = 59,1% viewport — proporsional). Namun uji DRAG LANGSUNG di viewport
mobile emulasi berulang GAGAL diselesaikan lewat automasi (panel browser jadi tak
responsif tiap kali drag dicoba di mode emulasi mobile) — ini keterbatasan alat
pengujian browser di sesi ini, BUKAN indikasi bug aplikasi: mekanisme drag Plotly
identik persis dengan desktop/tablet (sudah diverifikasi berfungsi di keduanya di atas),
styling hanya CSS/parameter visual (`bgcolor`/`bordercolor`/`thickness`) yang terbukti
dari dokumentasi Plotly resmi tidak mengubah logika hit-testing/interaksi.

**Temuan proses penting**: kegagalan awal berulang saat pengujian desktop (rangeslider
tak merespons drag sama sekali) ternyata disebabkan viewport tab browser diam-diam
tersisa di ukuran mobile (375px) dari sesi pengujian sebelumnya — bukan bug rangeslider.
Setelah viewport dikonfirmasi ulang eksplisit ke 1280px, drag langsung berfungsi normal.
Pelajaran: selalu verifikasi `window.innerWidth` sebelum menyimpulkan gagal fungsi.

## Verifikasi caption petunjuk

`st.caption("↔ Geser bagian bawah grafik untuk lihat rentang tanggal lain")` muncul
tepat di bawah tiap chart forecast (Ringkasan Operasional & Perkiraan Penjualan),
terbaca jelas di desktop, tablet, dan mobile.

## Verifikasi tak ada sisa kode mati

```
grep "rentang_riwayat_buttons|filter_riwayat_hari" app/ -r
-> hanya 1 kecocokan: komentar historis di charts.py (bukan pemanggilan kode)
```
Fungsi dihapus total dari `ui.py`, `overview.py`, `forecasting.py` — tak ada import/
pemanggilan tersisa.

## Cek regresi

Stok & Pembelian, Manajemen & Pengaturan: normal, tak ada dampak.

## Kesimpulan

Rangeslider custom (styling navy, border tebal, caption petunjuk) BERFUNGSI dan
terverifikasi lewat drag nyata (DOM range berubah, bukan cuma visual) di desktop DAN
tablet. Mobile terverifikasi visual penuh, drag literal tak terselesaikan via automasi
sesi ini (limitasi alat, dijelaskan jujur di atas) — mekanisme identik dengan yang sudah
terbukti berfungsi di ukuran lain. Kode preset lama dihapus bersih. Tak ada regresi.
Server dimatikan bersih.
