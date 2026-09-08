# Evidence — Perbaikan Visual Tahap A (risiko rendah, tak sentuh charts.py)

Tanggal: 8 September 2026

## Ringkasan perubahan

1. `views/pengaturan.py` — hapus 2 caption developer yang bocor ke pengguna:
   - Baris 239-240 (footer, tampil di semua tab): "Data tersimpan di database lokal
     (data/dss_umkm.db). Pada deployment, diganti PostgreSQL tanpa ubah kode (Sec.
     3.7.1)." — dihapus seluruhnya.
   - Baris 203-205 (Tab Catat Penjualan, di bawah tabel riwayat): "Mencatat penjualan
     memperkaya riwayat (lag/rolling)... Bobot model diperbarui via pelatihan ulang
     berkala..." — dihapus seluruhnya.
2. `app.py` + `components/ui.py` — redesain struktur sidebar:
   - Blok "Studi kasus"/"Rentang Waktu" dibungkus card `.sidebar-info` (border-kiri navy,
     radius 6px), gaya sama dengan `.kpi`/`.action`.
   - Watermark diganti dari `position:fixed` jadi bagian flow normal dalam
     `.sidebar-flex` (flex-column), didorong ke dasar via `margin-top:auto` — bukan
     ditempel paksa terlepas dari isi di atasnya.

## Insiden kecil saat testing (dilaporkan jujur)

Nilai awal `min-height:calc(100vh - 180px)` untuk `.sidebar-flex` ternyata KURANG
(perkiraan tinggi nav meleset) — watermark terpotong 74px di bawah viewport pada
pengujian pertama (1440×900). Diukur ulang lewat DOM: nav asli ~255px, bukan 180px.
Diperbaiki jadi `calc(100vh - 280px)` (margin aman di atas 255px terukur), lalu
diverifikasi ulang BERHASIL di semua ukuran layar (lihat hasil di bawah). Juga ditemukan:
auto-reload Streamlit TIDAK mengambil perubahan CSS secara otomatis (konsisten pelajaran
sesi-sesi sebelumnya) — proses di-restart penuh, bukan diandalkan hot-reload.

## Verifikasi caption bocor — HILANG (ekstraksi teks halaman penuh, bukan cuma visual)

Dicek lewat `get_page_text()` (ekstraksi SELURUH teks halaman) di Tab Catat Penjualan —
teks halaman berakhir tepat setelah "Riwayat penjualan (terbaru di atas):", TIDAK ADA
lagi kalimat jargon ML apa pun. Footer database dicek di tab Produk (representatif,
footer itu di luar semua tab) — TIDAK ADA, halaman berakhir setelah tombol "Simpan
Produk".

## Verifikasi sidebar (DOM langsung + visual, semua ukuran layar)

| Ukuran | `wmBottom` vs viewport | Hasil |
|---|---|---|
| Desktop (1440×900) | 875 < 900 | Watermark muat, tak terpotong. Card info tampil rapi dengan border-kiri navy. |
| Mobile (375×812) | 786.8 < 812 (sidebar overlay penuh) | Card + watermark muat sempurna, dikonfirmasi screenshot visual. |
| Tablet (768×1024) | 999 < 1024 | Muat sempurna. |

Diuji juga di halaman dengan konten LEBIH PENDEK (tab Produk, Manajemen & Pengaturan) —
sidebar tetap konsisten (layout sidebar independen dari panjang konten halaman utama,
sesuai desain `.sidebar-flex` yang berdiri sendiri).

## Cek regresi 4 halaman

Ringkasan Operasional, Perkiraan Penjualan, Stok & Pembelian, Manajemen & Pengaturan —
SEMUA dicek screenshot, sidebar baru konsisten tampil di semua, tak ada regresi konten
halaman utama.

## Kesimpulan

Tahap A selesai: 2 pelanggaran privasi-teknis (setara T-19) dihapus tuntas, struktur
sidebar diperbaiki di akar masalahnya (bukan cuma tambal visual). Satu nilai CSS meleset
di percobaan pertama, ditemukan & diperbaiki via pengukuran DOM sebelum dianggap selesai
— bukan diklaim benar tanpa verifikasi. `components/charts.py` TIDAK disentuh sama
sekali, sesuai scope Tahap A. Server dimatikan bersih.
