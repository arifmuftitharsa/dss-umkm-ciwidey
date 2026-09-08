# Evidence — Redesain Tahap 5 (TERAKHIR): Halaman Manajemen & Pengaturan

Tanggal pengujian: 8 September 2026

## Ringkasan perubahan

File PALING KOMPLEKS/SENSITIF di seluruh redesain (alur reset operasional T-1, form Catat
Penjualan). Audit menemukan halaman ini SUDAH otomatis konsisten sistem desain sejak
Tahap 1 (semua widget native: `st.data_editor`, `st.button`, `st.warning`, dst — otomatis
ikut `.streamlit/config.toml` + `.stDataFrame` CSS, tak ada HTML/CSS custom sama sekali di
file ini). Perubahan HANYA 2 baris teks, NOL logika/state disentuh:

1. `pengaturan.py:121` — label `st.checkbox()` konfirmasi reset operasional: em dash
   dihapus, jadi `"Saya paham, mulai catat data asli..."`.
2. `pengaturan.py:165` — `st.caption()` tanggal valid berikutnya: em dash dihapus, jadi
   `"...**{tanggal}**, pencatatan berurutan..."`.

Kedua perubahan murni parameter string ke widget yang sudah ada — signature widget, key,
kondisi `if`, urutan render TIDAK disentuh sama sekali.

## Temuan tambahan (dilaporkan, TIDAK dieksekusi — di luar 2 item yang disetujui)

`pengaturan.py:233` — `"Daftar hari libur & window efektif (2025–2026):"` pakai EN DASH
(U+2013, beda karakter dari em dash `—` yang biasa dicek grep sebelumnya) sebagai penanda
rentang tahun. Belum tercakup audit grep Tahap 2-4 (yang cuma cek `—`/`·`). Tidak diubah,
menunggu keputusan terpisah.

## PROTOKOL KEAMANAN — hasil eksplisit (WAJIB, sesuai kesepakatan)

Tab Catat Penjualan HANYA diobservasi visual (desktop + tablet), **TIDAK PERNAH** klik
tombol submit/simpan/aktivasi ("Mulai Pakai Data Real Hari Ini", "Catat Penjualan",
"Perbarui", "Hapus catatan terakhir") — tombol aktivasi dikonfirmasi dalam status
**disabled** (checkbox belum dicentang) sepanjang observasi.

Verifikasi dijalankan **DUA KALI** (setelah observasi desktop, dan lagi di akhir sesi
sebelum server dimatikan):

```
$ git status --porcelain app/data/historis_penjualan.csv
(kosong)

$ git diff app/data/historis_penjualan.csv
(kosong)
```

**Hasil: NOL perubahan pada `historis_penjualan.csv` sepanjang seluruh sesi testing.**
`dss_umkm.db` tetap tak ter-track (`.gitignore` sejak T-1), tak diverifikasi lewat git tapi
tak ada tombol simpan/tulis apa pun yang diklik di halaman manapun selama testing.

## Verifikasi checklist fitur — per tab

- **Tab 1 Produk**: `data_editor` border-radius terlihat (rounded), tombol "Simpan Produk"
  navy — otomatis benar TANPA kode tambahan, sesuai prediksi audit.
- **Tab 2 Bahan Baku & Stok**: konsisten, sama seperti Tab 1.
- **Tab 3 Resep (BOM)**: judul "Resep / Daftar Kebutuhan Bahan" tampil benar (perbaikan
  sesi sebelumnya masih utuh).
- **Tab 4 Catat Penjualan**: checkbox label baru tampil benar tanpa em dash (dicek desktop
  DAN tablet), warning kuning/amber native theme, tombol disabled state normal, tabel
  riwayat tampil rapi.
- **Tab 5 Window Libur**: tabel & tombol konsisten (temuan en dash dicatat terpisah di
  atas).

## Pengujian responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | `data_editor` tetap tampil fungsional (scroll internal bawaan komponen, keterbatasan diketahui, di luar scope perbaikan visual). Tombol full-width navy. Tab bar `st.tabs` native overflow horizontal dengan panah geser (perilaku bawaan Streamlit, bukan dibuat/diubah redesain ini). **Catatan jujur:** perpindahan otomatis ke tab "Catat Penjualan" via klik terprogram tidak berhasil diverifikasi ulang khusus di lebar 375px (widget tab canvas kurang presisi diklik lewat automation pada skala ini) — demi kehati-hatian (protokol keamanan), percobaan klik berulang di area itu DIHENTIKAN lebih awal daripada memaksa lewat trial-error dekat kontrol sensitif. Tab ini SUDAH diverifikasi visual penuh di desktop dan tablet. |
| Tablet (768×1024) | Semua 5 tab muat tanpa overflow. Tabel 5 kolom (Produk) rapi. Tab Catat Penjualan diverifikasi penuh (checkbox, warning, tombol disabled) — normal. |

## Cek regresi lintas halaman (pengecekan akhir seluruh 5 tahap redesain)

Ringkasan Operasional, Perkiraan Penjualan, Stok & Pembelian — dicek screenshot desktop,
SEMUA normal, tak ada regresi dari perubahan Tahap 5 maupun akumulasi Tahap 1-4.

## Kesimpulan

Tahap 5 (halaman Manajemen & Pengaturan, TERAKHIR dari 5 tahap redesain) selesai dengan
risiko terendah dari seluruh tahap — cuma 2 baris teks berubah, nol logika disentuh, nol
data tertulis tak sengaja (diverifikasi eksplisit 2×). Halaman ini terbukti sudah otomatis
konsisten sistem desain sejak Tahap 1 tanpa perlu kode CSS tambahan. Redesain visual UPStock
5 tahap (sistem desain dasar, Ringkasan, Perkiraan, Stok, Manajemen) SELESAI. Server
dimatikan bersih.
