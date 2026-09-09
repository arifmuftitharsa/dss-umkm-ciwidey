# Evidence — Audit & Perbaikan Bug HP Android Sungguhan (4 Temuan)

Tanggal: 9 September 2026

## Konteks — celah metodologi ditemukan

Seluruh pengujian mobile sebelumnya di proyek ini (audit 4 halaman) pakai simulasi
375px di browser desktop (Chrome DevTools/`resize_window`). Sesi ini ditemukan
simulasi TIDAK mereplikasi masalah yang muncul di HP Android sungguhan milik Arif —
4 temuan baru diverifikasi HANYA lewat screenshot/interaksi langsung di device fisik
via server Streamlit yang di-expose ke jaringan WiFi lokal (`--server.address=0.0.0.0`).

## Ringkasan 4 temuan

| # | Temuan | Status akhir |
|---|--------|--------------|
| 1 | Judul halaman "rusak"/terpotong di HP | **DIPERBAIKI** — bukan bug font, akar masalah beda total dari dugaan awal |
| 2 | Rangeslider chart terpotong tegas kanan | **DIPERBAIKI** — margin + padding ditambah |
| 3 | Tabel terpotong tanpa indikasi scroll | **BUKAN BUG** — scroll sudah berfungsi, cuma affordance visual kurang jelas |
| 4 | Tanda pisah "--"/"—" di teks pengguna | **DIPERBAIKI** (2 lokasi, audit menyeluruh) |

## Temuan 1 — Judul "rusak" — proses investigasi PANJANG, akhirnya bukan soal font

**Hipotesis yang DICOBA dan GAGAL** (masing-masing diverifikasi computed style benar
diterapkan di server, TAPI kerusakan visual di HP tetap sama persis):
1. `line-height:1.15` eksplisit di h1-h4
2. `letter-spacing` dihapus total (dugaan bug variable font + letter-spacing)
3. `text-size-adjust:100%` (dugaan font-boosting Android)
4. Google Fonts axis `opsz` diubah dari rentang ke titik tunggal (paksa static font,
   bukan variable) — DIPASANG lalu DICABUT lagi setelah terbukti bukan penyebab
5. `font-weight` diturunkan 600→500
6. Font diganti total ke `Georgia,serif` (sistem, BUKAN Google Font sama sekali) —
   TETAP rusak, ini titik balik penting: membuktikan bukan soal file font apa pun
7. `transition:none !important` di seluruh pembungkus (dugaan animasi kejepret
   screenshot) — DIPASANG lalu DICABUT lagi
8. Font diganti ke sans-serif (Plus Jakarta Sans, sama seperti body text) — TETAP
   rusak, membuktikan bukan soal serif vs sans-serif

**Tes isolasi krusial**: dicek apakah kerusakan yang sama muncul di situs LAIN
(Wikipedia, Medium) di HP yang sama — **YA, muncul juga**. Ini awalnya disimpulkan
"bug Chrome/OS milik Arif sendiri, di luar kendali kode" — SEMUA 8 percobaan di atas
sempat dicabut/dibersihkan berdasarkan kesimpulan ini.

**Akar masalah SEBENARNYA ditemukan lewat inspeksi DOM langsung** (bukan tebakan),
dipicu observasi Arif sendiri ("kotak putih persegi panjang di atas itu yang
menutupi"): `stHeader` — bar toolbar Streamlit (berisi tombol collapse sidebar) —
`position:absolute`, tinggi 60px, `background: rgb(255,255,255)` SOLID, `z-index:
999990`. `padding-top` `.block-container` SEBELUM perbaikan cuma `1.8rem` (28.8px,
desktop) dan malah `1rem` (16px) di mobile — jauh di bawah 60px. Konten (termasuk
judul h1/h2 PERTAMA di halaman) mulai jauh di atas garis aman, sehingga bar putih
solid itu MENIMPA bagian ATAS judul, memotong cap-height/ascender huruf pertama
baris pertama — persis pola "huruf pertama saja yang rusak, huruf lain normal" yang
dilaporkan berkali-kali.

Dikonfirmasi lewat `getBoundingClientRect()` langsung: `stHeader` rect
`{top:0, bottom:60}` tumpang tindih 28px dengan rect judul `{top:32}` SEBELUM
perbaikan; SESUDAH perbaikan (`padding-top:4.5rem`), judul mulai di `top:88`,
tanpa overlap sama sekali (jarak aman 28px).

**Kenapa 8 percobaan sebelumnya semua gagal**: karena diagnosis awal salah arah —
menduga soal PROPERTI font judul itu sendiri, padahal masalahnya elemen LAIN yang
menimpa dari luar. Baru ketahuan setelah threshold diagnosis diubah total: "elemen
APA yang overlap 20px teratas judul" (query `getBoundingClientRect()` semua elemen
body, filter yang overlap), bukan lagi utak-atik properti font.

**Perbaikan final**: `.block-container{padding-top:4.5rem}` (desktop DAN mobile,
tak lagi diturunkan di breakpoint mobile) — cukup jauh di atas 60px + buffer aman.

**Perbaikan tambahan setelah verifikasi**: ukuran font judul mobile (`h2`) dinaikkan
bertahap 1.4rem → 1.8rem → 2rem → 2.25rem → **2.6rem final** (lebih besar dari
desktop) sesuai permintaan Arif langsung di HP. Jarak judul-ke-subtitle juga
dirapikan (`h2{margin:0 0 .35rem !important; padding:0 !important}`,
`.section-sub{margin-top:0 !important}`) — sebelumnya Streamlit set `padding:1rem
0px` bawaan di h2 yang membuat jarak terlihat tak konsisten antar halaman
tergantung judul wrap 1 atau 2 baris.

**VERIFIKASI: DIKONFIRMASI LANGSUNG DI HP ANDROID SUNGGUHAN ARIF** (Chrome Android,
via WiFi lokal `http://192.168.1.100:8501`, BUKAN simulasi) — screenshot HP
menunjukkan judul bersih total di semua halaman (Ringkasan Operasional, Manajemen &
Pengaturan), tak ada tumpang tindih/potongan sama sekali, ukuran besar sesuai
preferensi Arif, jarak subtitle konsisten.

## Temuan 2 — Rangeslider terpotong tegas kanan

**Perbaikan**: dua lapis, sesuai instruksi Arif (coba solusi sederhana dulu, tanpa
remote-debug):
1. `charts.py` `forecast_chart()`: `margin.r` dinaikkan 10px → 22px (override lokal,
   TAK menyentuh `_LAYOUT` global yang dipakai chart lain tanpa rangeslider —
   konsisten pola `inventory_bar()` yang juga override margin sendiri, SRP: tiap
   chart atur ruang sesuai kebutuhannya).
2. `ui.py`: `[data-testid="stPlotlyChart"]{padding-right:.4rem}` khusus breakpoint
   mobile (`@media max-width:767px`) — ruang napas tambahan di LUAR canvas Plotly,
   jaga-jaga kalau elemen leluhur Streamlit yang clip di batas viewport (bukan
   Plotly-nya sendiri).

**VERIFIKASI: DIKONFIRMASI LANGSUNG DI HP ANDROID SUNGGUHAN ARIF** — screenshot
"Perkiraan Penjualan Produk Jus Stroberi Segar" menunjukkan rangeslider (kotak
navy bergaris di bawah grafik) sekarang punya ruang napas rapi di tepi kanan, tak
lagi terpotong tegas pas di batas layar.

## Temuan 3 — Tabel "terpotong" — TERNYATA BUKAN BUG

Diuji swipe langsung di 6 tabel/7 titik (Stok & Pembelian, Tab Produk, Bahan Baku,
Resep BOM, Catat Penjualan, Window Libur ×2) — **scroll horizontal sudah berfungsi
sejak awal di SEMUA tabel**. Masalah sebenarnya cuma soal AFFORDANCE VISUAL: tak ada
sinyal jelas ke pengguna bahwa tabel bisa digeser (scrollbar native Chrome Mobile
memang tersembunyi total, beda dari desktop yang tampilkan scrollbar tipis
persisten). **TIDAK PERLU perbaikan kode fungsional** — dicatat sebagai potensi
enhancement UX terpisah (indikator visual "bisa digeser"), TIDAK MENDESAK, di luar
scope perbaikan sesi ini.

## Temuan 4 — Tanda pisah teks pengguna (audit menyeluruh)

Grep menyeluruh seluruh `app/` (bukan cuma satu lokasi yang lolos audit sebelumnya)
untuk ` -- ` dan `—` di string literal TEKS PENGGUNA (bukan komentar kode/dev-only).
Ditemukan **DUA** pelanggaran nyata:

1. `views/pengaturan.py:134` (Tab Catat Penjualan, kartu "Sistem masih memakai data
   latihan") — sudah ditemukan Arif sebelumnya.
2. `data/record_sales.py:90` (pesan error `_validate_sequential`, muncul via
   `st.warning()` saat validasi tanggal Tab 4 gagal) — **BARU ditemukan** lewat
   audit menyeluruh, lolos dari review sebelumnya.

Placeholder `"---"`/`"—"` untuk nilai kosong/N-A (kolom Window, fallback nama
pemasok/label window) DIPERIKSA dan DIKONFIRMASI BUKAN pelanggaran — konvensi UI
berbeda (penanda "tak ada nilai"), bukan pengganti kata sambung kalimat.

Kedua lokasi diperbaiki: kalimat dipecah jadi dua kalimat terpisah tanpa tanda
pisah, arti tak berubah.

## Protokol keamanan data

```
$ git diff app/data/historis_penjualan.csv
(kosong)
```
Nol perubahan data production sepanjang seluruh sesi investigasi (termasuk saat
server di-expose ke jaringan WiFi untuk pengujian HP) — checkbox/tombol Tab 4 tak
pernah disentuh, semua interaksi cuma observasi visual dan navigasi baca.

## Smoke test regresi (server lokal biasa, BUKAN exposed-network)

- **Ringkasan Operasional** (desktop 1280px): kartu KPI, grafik forecast, kartu
  aksi, bar chart bahan baku — semua render normal, nol console error.
- **Manajemen & Pengaturan** (desktop 1280px): 5 tab, tabel Daftar Produk
  (P001-P003) utuh, nol console error.
- Visual desktop TAK berubah signifikan dari fix `padding-top`/`h2 margin` —
  dibandingkan screenshot sebelum-sesudah, tata letak konsisten.

## Verifikasi tak ada sisa server exposed-network

```
$ Get-CimInstance Win32_Process -Filter "CommandLine LIKE '%streamlit%app.py%'"
(kosong -- nol proses)
```
`.claude/launch.json` (gitignored) tak diubah sepanjang sesi ini (server
exposed-network dijalankan manual via Bash, bukan lewat entri launch.json
sementara seperti sesi-sesi sebelumnya).

## Kesimpulan

3 dari 4 temuan diperbaiki dengan kode, DIVERIFIKASI LANGSUNG di HP Android
sungguhan Arif (bukan simulasi desktop) — bukti paling kuat sepanjang proyek ini
karena inilah kali pertama celah metodologi "simulasi tak mereplikasi device asli"
ditemukan dan diatasi dengan pengujian device fisik sungguhan lewat WiFi lokal.
Temuan 3 diverifikasi BUKAN bug, cuma soal affordance — dicatat jujur tanpa
memoles jadi "bug" supaya terlihat produktif. Proses Temuan 1 sangat panjang (10
putaran investigasi) karena diagnosis awal salah arah (soal font) — pelajaran
untuk audit HP berikutnya: cek overlap elemen (`getBoundingClientRect()`) LEBIH
DULU sebelum menduga-duga properti CSS spesifik elemen yang dilaporkan rusak.
