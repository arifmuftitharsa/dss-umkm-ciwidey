# Evidence — Redesain Tahap 1: Sistem Desain Dasar

Tanggal pengujian: 8 September 2026

## Ringkasan perubahan

1. `config.py`: `WARNA` dict diganti token netral (navy `#1E3A5F` sebagai aksen, slate
   `#64748B` sekunder, status kritis/waspada/aman diperbarui `#DC2626`/`#D97706`/`#16A34A`,
   `bg`/`kartu` putih `#FFFFFF`, tambah `surface` `#F7F8FA` khusus chrome sidebar). Kunci dict
   TAK berubah — `components/charts.py` otomatis ikut warna baru tanpa disentuh sama sekali.
2. `.streamlit/config.toml`: disinkronkan ke token yang sama (di luar daftar eksplisit
   instruksi, tapi jelas bagian dari "sistem desain dasar" — kalau tak disinkron, widget asli
   Streamlit seperti tombol tetap warna lama sementara kartu custom sudah navy).
3. `components/ui.py`: CSS dirombak — kartu KPI & action-card ganti dari shadow+radius besar
   jadi border-kiri berwarna (radius kecil 6px), label ALL-CAPS dihapus jadi sentence case,
   tambah breakpoint `@media` 1023px & 767px (kartu KPI ditumpuk vertikal di mobile via
   override `stHorizontalBlock`). Sekalian dibersihkan: CSS `.stRadio` mati (nav radio sudah
   diganti `st.navigation`).
4. `app.py`: migrasi dari `st.radio` manual ke `st.navigation()`/`st.Page()` — 4 halaman
   dibungkus fungsi tanpa argumen (closure atas `df`), isi `views/*.py` TAK disentuh. Watermark
   sidebar "Prototipe penelitian S1 · bukan data produksi" diganti koma (titik-tengah
   dihapus, lokasi dikonfirmasi ADA di app.py sebelum eksekusi). Hex warna inline lama
   (`#1B4965`, `#6B7785`) disinkronkan ke `WARNA` dict (DRY, satu sumber kebenaran).

## Verifikasi checklist fitur (tak ada yang hilang)

- **Ringkasan Operasional**: 3 KPI, grafik forecast produk utama, panel "Yang Perlu
  Dilakukan" (kartu aksi kritis/info), grafik bar stok — SEMUA ADA, diverifikasi via
  screenshot desktop & tablet.
- **Perkiraan Penjualan**: dropdown produk, dropdown rentang waktu, 2 KPI, grafik — SEMUA
  ADA.
- **Stok & Pembelian**: 3 KPI, Daftar Belanja (kartu aksi), tabel status pill, grafik bar —
  SEMUA ADA (scroll dicek, tabel `Kondisi Semua Bahan Baku` tampil dengan pill warna benar).
- **Manajemen & Pengaturan**: SEMUA 5 tab ada (Produk, Bahan Baku & Stok, Resep BOM, Catat
  Penjualan, Window Libur). Tab Produk: tabel `data_editor` + tombol simpan (warna navy,
  konfirmasi sinkron `.streamlit/config.toml`). Tab Catat Penjualan: alur reset operasional
  (checkbox konfirmasi + tombol, state T-1) tetap berfungsi normal, tabel riwayat tampil.

## Verifikasi visual sistem desain

- Kartu KPI: border-kiri navy terlihat jelas, TANPA shadow — dikonfirmasi di semua ukuran
  layar diuji.
- Label KPI/section: sentence case, ALL-CAPS terkonfirmasi hilang.
- Watermark sidebar: `"Prototipe penelitian S1, bukan data produksi"` — tanpa titik-tengah.
- Tombol primary (`Simpan Produk`, dst): warna navy `#1E3A5F` — konfirmasi
  `.streamlit/config.toml` tersinkron dengan `config.py`.
- Action card (Daftar Belanja, Yang Perlu Dilakukan): border-kiri merah/navy sesuai level,
  konsisten dengan KPI card.

## Pengujian responsif

| Ukuran | Hasil |
|---|---|
| Desktop (1440×900) | Sidebar + nav + konten normal, 3 kolom KPI sejajar, tak ada elemen terpotong. |
| Tablet (768×1024) | Sidebar auto-collapse (native Streamlit), 3 KPI tetap sejajar rapi tanpa overflow dalam lebar 768px. |
| Mobile (375×812) | Sidebar mulai dalam kondisi terbuka (`initial_sidebar_state="expanded"`, pengaturan lama tak diubah tahap ini) — **dicek toggle collapse ("»") berfungsi**: sidebar berhasil collapse via klik, konten jadi full-width. KPI card TERKONFIRMASI ditumpuk vertikal (CSS `@media max-width:767px` bekerja — override `flex-direction:column` pada `stHorizontalBlock`). Grafik bar & action card di halaman Ringkasan tetap utuh, tak ada elemen terpotong, dicek sampai scroll ke bawah (grafik "Kondisi Stok Bahan Baku").

### Catatan jujur soal klaim "adaptif ke hamburger"

`st.navigation()` di posisi mobile TIDAK otomatis mulai dalam keadaan tertutup — itu
dikontrol terpisah oleh `initial_sidebar_state="expanded"` di `st.set_page_config()` (tak
diubah di Tahap 1 ini, sesuai instruksi "jangan sentuh yang tak perlu"). Yang terkonfirmasi:
toggle collapse BEKERJA (klik "»" berhasil menyembunyikan sidebar sepenuhnya, `aria-expanded`
berubah ke `false`, lebar elemen jadi ~0px) — jadi "adaptif" di sini berarti tersedia
mekanisme collapse manual yang berfungsi, BUKAN auto-collapse tanpa interaksi pengguna saat
pertama buka di HP. Kalau auto-collapse di mobile diinginkan, itu perubahan satu baris
(`initial_sidebar_state="auto"`) yang belum dieksekusi karena di luar apa yang diminta
eksplisit di Tahap 1 — dilaporkan sebagai potensi perbaikan Tahap 2+ atau butuh keputusan
terpisah, bukan diam-diam diubah sekarang.

## Navigasi

Diklik-klik ke semua 4 halaman via `st.navigation()` baru (desktop) — perpindahan halaman
normal, tak ada error. Tab Catat Penjualan (state paling kompleks, alur reset operasional)
dicek tetap utuh setelah migrasi navigasi.

## Kesimpulan

Tahap 1 (sistem desain dasar: token warna, CSS responsif, migrasi navigasi) selesai dan
terverifikasi di 3 ukuran layar. Tak ada fitur yang hilang dari checklist. Server dimatikan
bersih setelah pengujian. `views/*.py` (isi 4 halaman) TIDAK disentuh sesuai rencana — Tahap
2–5 menyusul terpisah.
