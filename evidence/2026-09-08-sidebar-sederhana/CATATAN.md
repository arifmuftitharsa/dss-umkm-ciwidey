# Evidence — Sidebar disederhanakan (hapus card info + watermark)

Tanggal: 8 September 2026

## Ringkasan perubahan

Sesuai keputusan Arif, 3 elemen dihapus TOTAL dari sidebar (`app.py`):
1. Card "Studi kasus" (lokasi Ciwidey dst).
2. Card "Rentang Waktu" (penjelasan horizon 7/14/30 hari).
3. Watermark "Prototipe penelitian S1, bukan data produksi".

Struktur sidebar baru: nav 4 halaman (bawaan `st.navigation`) → garis pemisah → nama
"UPStock" + tagline "Bantu UMKM Kelola Stok" → SELESAI.

**CSS disederhanakan**: `.sidebar-flex` (flex-column + `min-height` perhitungan viewport),
`.sidebar-info` (card border-kiri), `.sidebar-watermark` (margin-top:auto) — SEMUA dihapus
dari `components/ui.py`. Dicek dulu lewat grep: ketiga class HANYA dipakai di `app.py`,
aman dihapus tanpa dampak ke file lain. Alasan hapus (bukan cuma ganti isi): tanpa elemen
yang perlu "didorong ke dasar", kompleksitas flex-column+margin-auto jadi tak relevan lagi
— clean code berarti hapus yang tak dipakai, bukan biarkan menumpuk.

**Import mati**: `STUDI_KASUS` di `app.py` jadi tak terpakai setelah card dihapus (dulu
dipakai untuk teks lokasi) — dihapus dari `from config import ...`.

## Keputusan: disclaimer riset dipindah dari UI, BUKAN dihapus dari kesadaran proyek

Watermark "Prototipe penelitian S1, bukan data produksi" adalah bagian dari prinsip T-15
(sistem berbasis data sintetis, bukan data produksi tervalidasi — jangan sebut akurasi ke
UMKM tanpa konteks). Menghapusnya dari UI TIDAK berarti prinsip T-15 gugur — tanggung
jawab menyampaikan status riset ini dipindah ke **dokumentasi** (`docs/`, direncanakan
Minggu 4 sesuai CLAUDE.md) dan **penjelasan lisan langsung ke pemilik UMKM saat
onboarding**, bukan lewat teks kecil di sidebar yang sering diabaikan pengguna awam.
Keputusan ini dicatat di sini sebagai jejak — bukan tindak lanjut kode di tugas ini,
sesuai instruksi eksplisit.

## Verifikasi 4 halaman (desktop)

Ringkasan Operasional, Perkiraan Penjualan, Stok & Pembelian, Manajemen & Pengaturan —
SEMUA dicek screenshot: sidebar konsisten ringkas (nav + garis + nama + tagline), tak ada
elemen terpotong, tak ada sisa layout aneh dari penghapusan.

## Pengujian responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | Sidebar tampil rapi, tak ada elemen rusak/terpotong. Ruang kosong di bawah nav memang lebih besar dari sebelumnya (konten jauh lebih sedikit) — ini KONSEKUENSI YANG SUDAH DITERIMA secara eksplisit oleh Arif (instruksi: "tidak ada elemen yang perlu didorong ke dasar"), bukan cacat. |
| Tablet (768×1024) | Sama — rapi, konsisten, tak ada masalah. |

## Kesimpulan

Sidebar berhasil disederhanakan sesuai spesifikasi persis: nama+tagline+nav, tak lebih.
Kompleksitas CSS Tahap A (flex-column, margin-auto, card) dibersihkan tuntas karena sudah
tak relevan dengan struktur baru — bukan ditinggalkan sebagai dead code. Disclaimer riset
T-15 tetap berlaku sebagai prinsip proyek, tanggung jawabnya dipindah ke dokumentasi/lisan.
Tak ada regresi di 4 halaman maupun 2 ukuran layar diuji. Server dimatikan bersih.
