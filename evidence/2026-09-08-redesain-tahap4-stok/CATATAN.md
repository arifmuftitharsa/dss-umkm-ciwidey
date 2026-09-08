# Evidence — Redesain Tahap 4: Halaman Stok & Pembelian

Tanggal pengujian: 8 September 2026

## Ringkasan perubahan

Beda dari Tahap 2-3, halaman ini punya elemen HTML custom (tabel `to_html()` dengan status
pill) yang lepas dari mekanisme otomatis `st.dataframe()`/`ui.py` — butuh penyesuaian kode,
bukan cuma teks.

1. **`components/ui.py`** — tambah helper `_tint(hex, alpha)` (hitung rgba dari token,
   pola sama dengan `charts._rgba` di Tahap 2). Background pill status (`.pill.kritis/
   .waspada/.aman`) dulu hex hardcoded (`#FBE6E9`/`#FBF0DE`/`#E2F3EC`, cocok warna LAMA
   sebelum Tahap 1) — diganti `_tint(WARNA['kritis'/'waspada'/'aman'], .12)`, dihitung dari
   token yang SAMA dengan `color`, dijamin ikut kalau token berubah lagi.
2. **`components/ui.py`** — tambah CSS `.tabel-scroll` (wrapper untuk tabel HTML custom):
   `overflow-x:auto`, border & border-radius konsisten `var(--garis)`/8px (sama dengan
   `.stDataFrame`), styling `th`/`td` (padding, header pakai `var(--surface)`).
3. **`views/inventory.py`** — bungkus output `to_html()` dengan `<div class="tabel-scroll">`.
4. **`views/inventory.py`** — em dash di judul kartu aksi (baris 45) dan titik-tengah di
   caption (baris 67) dihapus, ganti koma. `±` dikonfirmasi bukan tanda pisah, dibiarkan.

Keputusan desain (disetujui sebelum eksekusi): pertahankan tabel HTML custom (Opsi a),
bukan ganti ke `st.dataframe()`, karena pill berwarna adalah fitur eksplisit di checklist
Tahap 1 yang tak boleh hilang — `st.dataframe()` native tak bisa render HTML/warna per sel
dengan mudah.

## Verifikasi checklist fitur

3 KPI (Bahan Dipantau, Perlu Dibeli, Stok Aman), Daftar Belanja Minggu Ini (kartu aksi),
tabel HTML kondisi bahan (status pill), grafik bar posisi stok, expander tabel kebutuhan
bahan per hari — SEMUA ADA.

## Verifikasi warna pill (DOM langsung, bukan visual)

```js
document.querySelectorAll('.pill') -> getComputedStyle
```
- "Segera beli": `background: rgba(220,38,38,0.12)`, `color: rgb(220,38,38)` — `#DC2626`
  (token `kritis`), background & teks SAMA basis warna.
- "Aman" (5×): `background: rgba(22,163,74,0.12)`, `color: rgb(22,163,74)` — `#16A34A`
  (token `aman`), konsisten.

## Verifikasi tabel HTML (DOM langsung)

```js
document.querySelector('.tabel-scroll') -> getComputedStyle
```
`borderRadius: "8px"`, `border: "0.8px solid rgb(229, 231, 235)"` (`#E5E7EB` = `var(--garis)`),
`overflowX: "auto"` — terkonfirmasi, bukan lagi border browser default 1px hitam.

## Pengujian responsif — verifikasi NYATA, bukan asumsi

**Mobile (375×812)**: dicek lewat DOM — `wrapWidth: 349px`, `tableScrollWidth: 695px` →
`needsScroll: true` (overflow sungguhan terjadi, bukan kebetulan muat). Uji scroll nyata:
`wrap.scrollLeft = 200` → `scrollLeft` benar-benar berubah jadi `200` — mekanisme scroll
horizontal BERFUNGSI, dikonfirmasi via DOM + screenshot visual (kolom "Bahan Baku" tergeser
ke kiri layar setelah discroll).

**Tablet (768×1024)**: tabel 6 kolom muat PENUH tanpa scroll, semua kolom sejajar rapi,
pill tampil normal.

## Verifikasi tanda pisah

- Kartu aksi "Daftar Belanja Minggu Ini": `"Stroberi Segar, beli ± 135 kg"` — koma, `±`
  tetap ada (bukan tanda pisah, sesuai konfirmasi). Hanya 1 bahan baku perlu dibeli di
  dataset ini (Stroberi Segar) — varian lain tak bisa diuji karena data tak menghasilkannya,
  tapi kode identik untuk semua baris loop, risiko rendah.
- Caption: `"Batas aman = ROP (titik pesan ulang), jumlah beli ideal = EOQ (kuantitas
  optimal sekali pesan)."` — koma, tanpa titik-tengah.

## Cek regresi halaman lain

Ringkasan Operasional, Perkiraan Penjualan, Manajemen & Pengaturan — dicek screenshot,
SEMUA normal, tak ada regresi dari perubahan `ui.py` (CSS `.tabel-scroll`/`_tint` cuma
berlaku pada elemen yang memakainya, tak memengaruhi komponen lain).

## Kesimpulan

Tahap 4 (halaman Stok & Pembelian) selesai. Bug warna pill (sama kelas dengan bug Tahap 2)
diperbaiki, tabel HTML custom sekarang konsisten sistem desain + responsif (diverifikasi
DOM, bukan diasumsikan), 2 tanda pisah dihapus. Tak ada fitur hilang, tak ada regresi.
Server dimatikan bersih.
