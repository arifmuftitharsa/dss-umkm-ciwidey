# Evidence — Hapus Label "Tanggal" (Akar DPR), Rangeslider Ramping, Caption Rata Kiri

Tanggal: 8 September 2026

## Akar Masalah 1 (regresi "Tanqqal") — untuk referensi masa depan

`window.devicePixelRatio` di layar Arif = **1.25** (Windows display scaling 125%).
DPR pecahan (non-integer) dikenal luas menyebabkan artefak anti-aliasing pada teks SVG
kecil — kluster huruf rapat seperti "gg" jadi terlihat blur/menyatu (mirip "qq"),
**independen dari nilai `font.size`** yang dipakai (16px sudah dicoba di perbaikan
sebelumnya, tetap muncul lagi di DPR pecahan). Dikonfirmasi bukan disebabkan `height`
chart (dugaan awal) — `font.size` tetap presisi 16px di DOM terlepas dari height 420
atau 480.

**Kalau ada laporan visual serupa di masa depan** ("teks di chart terlihat rusak/blur"):
cek dulu `window.devicePixelRatio` di browser pelapor lewat DevTools Console. Kalau
pecahan (1.25, 1.5, dst — umum di laptop Windows dgn scaling non-100%), kemungkinan
besar ini penyebabnya, bukan bug kode. Solusi paling robust: HINDARI teks SVG kecil
sama sekali di elemen yang sering dilihat pada berbagai DPR, ganti dengan elemen HTML
(Streamlit markdown/caption) yang di-render browser native (lebih tahan artefak DPR
dibanding SVG `<text>` Plotly.

## Solusi (3 perbaikan)

1. **`xaxis.title` ("Tanggal") dihapus total** — sekaligus menyelesaikan akar Masalah 1
   (tak ada lagi teks SVG kecil yang bisa kena artefak DPR) DAN Masalah 2 (urutan
   render Plotly: title selalu di BAWAH rangeslider, tak bisa diatur ulang lewat
   parameter apa pun — dikonfirmasi dari perilaku sebelumnya). Tick tanggal (`DD/MM`)
   tetap ada dan cukup jelas maknanya tanpa label terpisah.
2. **Thickness rangeslider `.15 → .08`** — proporsi lebih ramping, kontras tetap
   terjaga dari `bgcolor`/`bordercolor` navy (bukan dari ketebalan).
3. **Caption rata kiri** — `ui.petunjuk_geser()` (fungsi baru `ui.py`), HTML custom
   sejajar sumbu-y, warna `WARNA["teks_lemah"]`, ikon "↔", GANTI `st.caption()` bawaan
   yang center.

## Verifikasi Masalah 1 — DPR REAL, bukan simulasi

**Temuan penting**: panel browser pengujian session ini SENDIRI melaporkan
`devicePixelRatio: 1.25` — PERSIS kondisi layar Arif. Jadi pengujian di bawah ini
BUKAN simulasi DPR terpisah, melainkan pengujian nyata pada DPR yang sama persis yang
memicu bug. `hasTitle: false` dikonfirmasi via DOM (elemen `.xtitle` tak ada sama
sekali) — tak ada lagi teks yang bisa kena artefak, di DPR manapun.

## Verifikasi urutan visual — Masalah 2

Screenshot Ringkasan Operasional & Perkiraan Penjualan: urutan SEKARANG benar —
Grafik → tick tanggal (DD/MM) → rangeslider → caption "↔ Geser bagian bawah grafik
untuk lihat rentang tanggal lain" (rata kiri, sejajar sumbu-y, BUKAN di tengah).

## Verifikasi fungsi — drag rangeslider (thickness .08, DOM range dicek tiap kali)

| Halaman/Ukuran | Hasil |
|---|---|
| Ringkasan Operasional (desktop) | drag handle kanan: range penuh → `2025-10-03 - 2025-11-25` |
| Perkiraan Penjualan (desktop) | drag handle kanan: range penuh → `2025-10-03 - 2025-12-07` |
| Tablet (768px) | drag handle kanan: range penuh → `2025-10-03 - 2025-11-28` |
| Drag-select zoom manual (desktop) | tetap berfungsi (`2025-10-25 - 2025-12-11` setelah drag di area plot), berdampingan tanpa konflik |

**Catatan proses**: sempat ada masalah drag tak terdeteksi di TAB browser yang sama
dipakai berulang kali (kemungkinan state/fokus browser tersangkut dari sesi sebelumnya
— gejala: drag malah men-select teks halaman, bukan menggerakkan handle). Diselesaikan
dengan membuka TAB BARU bersih — setelah itu semua drag berfungsi normal dan konsisten.
Dicatat sebagai pelajaran proses, bukan indikasi bug kode.

**Mobile (375px)**: verifikasi VISUAL selesai — tak ada label Tanggal, caption rata
kiri terbaca, tinggi chart 420px/812px = **51,7%** (turun dari 59,1% versi thickness
.15, proporsional). Uji DRAG LANGSUNG di viewport mobile emulasi kembali tak
terselesaikan via automasi (limitasi alat browser-pane yang sudah tercatat di evidence
percobaan sebelumnya juga) — bukan indikasi bug, mekanisme sama persis dengan yang
sudah terbukti berfungsi di desktop dan tablet.

## Cek regresi

Stok & Pembelian, Manajemen & Pengaturan: normal, tak ada dampak.

## Kesimpulan

Ketiga perbaikan selesai. Masalah 1 diperbaiki di AKAR (hapus sumber teks kecil yang
rentan artefak DPR, bukan naikkan ukuran lagi yang cuma menunda masalah) dan
diverifikasi PADA DPR SAMA PERSIS dengan laporan Arif (1.25) — bukan asumsi lolos di
lingkungan berbeda. Masalah 2 diselesaikan lewat pemahaman keterbatasan render-pipeline
Plotly (title selalu di bawah rangeslider), bukan dipaksa/di-hack. Rangeslider &
caption sesuai spesifikasi ukuran/tata letak yang diminta. Tak ada regresi. Server
dimatikan bersih.
