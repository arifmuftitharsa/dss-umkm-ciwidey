# CLAUDE.md — DSS UMKM Alamendah

Ini proyek pengabdian masyarakat/skripsi kakak tingkat (Felix Joshua Paulus, 105222032) yang
sedang dilanjutkan oleh Arif: perbaikan kode, deployment, dokumentasi, onboarding pengguna.

**Sumber kebenaran lengkap ada di `brief/BRIEF-PROYEK-DSS-UMKM-v6.md` di folder ini — baca file
itu dulu sebelum menjawab pertanyaan substantif soal skripsi, temuan bug, atau rencana kerja.**
File ini (`CLAUDE.md`) hanya ringkasan supaya kamu tidak mulai dari nol tiap sesi.

## Ringkasan super singkat

Sistem: Streamlit + SQLite + XGBoost, prediksi kebutuhan stok bahan baku UMKM olahan stroberi
(Ciwidey). Skripsi sumber pakai data 100% sintetis. Prototipe belum pernah deploy daring.

## 15 temuan (T-1 s.d. T-15) — status per direktori

Detail penuh tiap temuan ada di brief. Ringkasan cepat:

| # | Temuan | Prioritas |
|---|--------|-----------|
| T-1 | `data/record_sales.py` kunci tanggal di 2025-12-31, tolak lompatan. **✅ SELESAI 5 Sept (commit a6cdeb1)** — Opsi B: titik reset eksplisit (tabel `pengaturan_sistem`), filter riwayat pasca-reset di forecasting.py, bug widget UI diperbaiki | KRITIS — **SELESAI** |
| T-2 | `core/forecasting.py` tambah noise acak ke prediksi. **✅ SELESAI 5 Sept (commit e903dd0)** — noise dihapus; terbukti noise SUDAH deterministik sejak awal (bukan penyebab variasi 502/498, itu T-7b) | KRITIS — **SELESAI** |
| T-3 | Sigma/safety stock dari konstanta literatur, bukan error model nyata | TINGGI — **BELUM, menunggu keputusan Bu Ariana** |
| T-4 | Produk baru via dashboard: KeyError, tidak masuk hitungan bahan. **✅ SELESAI 5 Sept (commit fe1f732)** — scope meluas ke 5 file (core/ + views/), plus 2 bug tambahan ditemukan & diperbaiki (NaT crash, chart crash riwayat kosong), plus hardcode pid_utama P003 | KRITIS — **SELESAI** |
| T-5 | GUGUR — scaler aman, sudah dibungkus Pipeline di `.joblib` | selesai, tidak perlu kerja |
| T-6 | GUGUR — CSV vs SQLite bukan konflik sumber, pembagian sudah benar | selesai |
| T-7 | GUGUR — fallback cuaca luring sudah ada dan bagus | selesai (T-7b masih ada, lihat bawah) |
| T-7b | Bug penyelarasan tanggal cuaca saat forecast_future. **✅ SELESAI 5 Sept (commit 6a05219)** — percabangan live-API vs klimatologi, flag `used_climatology` disiapkan untuk Minggu 3 | **SELESAI** |
| T-8 | `requirements.txt` hilang xgboost/joblib/holidays/requests/scikit-learn. **✅ SELESAI 4 Sept (commit 8ddd1c0)** — xgboost/sklearn dipin persis, lainnya floor | TINGGI — **SELESAI** |
| T-9 | Tanpa autentikasi, storage ephemeral (data hilang saat redeploy) | SEDANG-BESAR — belum, rencana Minggu 3 |
| T-10 | Angka evaluasi palsu di kode (`_EVAL_RESULTS`, `simulasi_skenario`) — kode mati, tak tampil, tapi repo publik | MENENGAH — hapus saja, belum dikerjakan |
| T-11 | `config.py` beda dari skripsi (harga, BOM, kode bahan) | MENENGAH — akan diganti data mitra asli |
| T-12 | Batas lot EOQ (Persamaan 3.11) tidak diimplementasikan, `shelf_life` tidak ada | SEDANG — **BELUM, menunggu keputusan Bu Ariana bareng T-3** |
| T-13 | Startup regenerasi dataset sintetis 3 tahun, tidak dipakai (`forecast_future` baca CSV, bukan df) | RENDAH |
| T-14 | Output `dss-model` masih ARIMA (32%), skripsi laporkan ARIMAX (8-9%) — perlu run_pipeline.py ulang | RENDAH |
| T-15 | Model dilatih 100% data sintetis — jangan sebut akurasi ke UMKM | selalu berlaku |
| T-16 | Formula demand di `generate_dataset.py` multiplicative, skripsi Pers. 3.1 tulis aditif — beda struktur matematis | RENDAH, akademis saja |
| T-17 | `holidays==0.98` di repo vs 0.101 diverifikasi skripsi; nama file `requirementsumkm.txt` bukan `requirements.txt` | RENDAH |
| T-18 | Repo tak 100% reproduksi Tabel 4.7 (demand P001) walau seed=42 sama — kode direvisi setelah tabel final skripsi dibuat | RENDAH, jangan asumsikan retraining = angka skripsi identik |
| T-19 | Kartu "Akurasi 92%/92,1%" tampil mencolok ke pengguna di 2 halaman. **✅ SELESAI 5 Sept (commit b70209b)** — dihapus total (Opsi A), docstring asli file sudah menjanjikan "tanpa istilah teknis" | TINGGI — **SELESAI** |
| T-20 | `pandas`/`numpy` floor version resolve ke lompatan mayor (pandas 2.x→3.0.5) belum diuji, sama pola risiko dengan alasan pin xgboost/sklearn | SEDANG — belum diverifikasi/dipin |

**Status per 5 September 2026: SEMUA KRITIS/TINGGI selesai kecuali T-3/T-12 (menunggu
keputusan Bu Ariana) dan T-20 (belum mendesak). Progress report ke Bu Ariana jadi prioritas
berikutnya sebelum lanjut kerja teknis lain.**

## Status commit progres (update tiap ada commit baru)

| Commit | Isi | Tanggal |
|--------|-----|---------|
| `9e81251` | Commit pertama, gabungan app/model/dataset-gen | 4 Sept 2026 |
| `0865103` | Tambah README.md (riwayat + atribusi) | 4 Sept 2026 |
| `8ddd1c0` | T-8: requirements.txt lengkap (xgboost/sklearn dipin persis, lainnya floor) | 4 Sept 2026 |
| `638ae7a` | Rapikan struktur evidence, update CLAUDE.md dengan T-19/T-20 dan revisi T-1 | 4 Sept 2026 |
| `e903dd0` | T-2: hapus noise acak forecasting (noise sudah deterministik sejak awal) | 5 Sept 2026 |
| `6a05219` | T-7b: perbaiki mismatch tanggal cuaca, fail-fast except, flag used_climatology | 5 Sept 2026 |
| `a6cdeb1` | T-1: titik reset operasional, filter riwayat pasca-reset, .gitignore untuk db | 5 Sept 2026 |
| `b70209b` | T-19: hapus kartu akurasi, rapikan layout kolom | 5 Sept 2026 |
| `fe1f732` | T-4: cold start produk baru (5 file), bug NaT + chart crash + hardcode P003 | 5 Sept 2026 |

Evidence "sebelum perbaikan" direkam SEBELUM T-1/T-2 disentuh — evidence bersifat write-once,
jangan diedit setelah direkam.

## Aturan kerja (sama seperti project Claude.ai)

1. Jangan mengarang isi kode. Baca berkas asli sebelum menyimpulkan.
2. Benar sebelum indah — jangan poles UI sebelum T-1/T-2 (blocker demo) beres.
3. Semua teks yang dilihat pengguna akhir: Bahasa Indonesia sehari-hari, tanpa jargon.
4. Jangan sebut angka akurasi model (92%, MAPE) ke pelaku UMKM di lapangan.
5. Debugging/edit kode yang sudah jalan → full file rewrite siap pakai, bukan snippet.
6. Belajar konsep baru dari nol → guided learning, logika dulu.
7. Perubahan besar butuh bukti sebelum-sesudah (screenshot atau angka) untuk laporan.
8. Kalibrasi inventori (T-3, T-12), skala tenant, dan status akademis pekerjaan ini —
   **sudah final**: ini BUKAN skripsi Arif, murni pengabdian masyarakat (lihat Bagian 6
   brief poin #9). Kalibrasi inventori masih menunggu keputusan siapa mengerjakan.
9. **Clean Code dan SOLID Principles WAJIB diterapkan ketat pada setiap kode yang ditulis
   atau diedit** — ini bukan preferensi opsional, ini syarat wajib:
   - Single Responsibility: satu fungsi/kelas satu tanggung jawab. Kalau satu fungsi
     melakukan lebih dari satu hal (misal: ambil data DAN hitung DAN format tampilan),
     pecah jadi beberapa fungsi.
   - Open/Closed: struktur kode agar penambahan fitur baru (misal produk baru, temuan
     T-4) tidak memaksa mengubah logika inti yang sudah teruji — perluas, jangan modifikasi
     yang sudah benar.
   - Liskov, Interface Segregation, Dependency Inversion: relevan terutama kalau ada
     abstraksi/kelas — jangan buat interface gemuk, jangan hardcode dependency konkret
     kalau bisa di-inject.
   - Penamaan variabel/fungsi jelas dan deskriptif (hindari nama seperti `df`, `x`, `tmp`
     kalau konteksnya penting dipahami pembaca lain).
   - Hindari magic number/string — jadikan konstanta bernama (lihat T-3: `mape_ref` hardcoded
     adalah contoh pelanggaran ini yang harus dihindari saat menulis kode baru).
   - Setiap kali menulis atau mengedit kode, tunjukkan secara eksplisit bagaimana perubahan
     itu menerapkan prinsip di atas — jangan asumsikan sudah otomatis clean tanpa dijelaskan.
   - Kalau kode existing yang diperbaiki (misal saat mengerjakan T-1/T-2/T-3/T-12) melanggar
     SOLID/clean code, perbaiki sekalian strukturnya, bukan cuma tambal fungsional — tapi
     laporkan dulu rencana refactor-nya sebelum eksekusi, jangan diam-diam mengubah struktur
     besar tanpa approval.

## Delapan prinsip rekayasa perangkat lunak — WAJIB dipertimbangkan sebelum planning & coding

Ini bukan daftar opsional untuk dipilih sebagian — pertimbangkan SEMUA delapan ini setiap kali
akan membuat plan atau menulis kode, walau kesimpulannya "belum relevan di tahap ini".

1. **C4 Model (dokumentasi arsitektur)** — 4 level: Context, Container, Component, Code.
   Prinsip: gambar/dokumentasi berbeda untuk audiens berbeda (stakeholder non-teknis vs
   developer baru vs orang yang baca kode langsung). Saat menulis dokumentasi arsitektur
   proyek ini (Minggu 4, brief Bagian 5), strukturkan mengikuti level ini, jangan campur
   semua level jadi satu dokumen datar.

2. **CI/CD** — Build → Test otomatis (CI) → Release + Deploy (Delivery/Deployment). Tools
   untuk Python: pytest untuk testing. Sebelum deploy ke hosting (Minggu 3), pertimbangkan
   pipeline ini walau sesederhana GitHub Actions dasar — jangan deploy manual tanpa test
   otomatis kalau ada waktu untuk setup ini.

3. **Testing prioritas berdasarkan risiko** — bukan asal test semua fungsi. Fokus ke fungsi
   yang PALING KRITIS atau yang PERNAH jadi sumber bug. Untuk proyek ini: prioritas testing
   ada di modul yang sudah terbukti jadi sumber masalah — `core/inventory.py` (T-3, T-12,
   sumber stockout 78%), `core/forecasting.py` (T-2, noise acak), `data/record_sales.py`
   (T-1, blocker demo). Jangan buang waktu test exhaustive ke bagian UI yang low-risk dulu.

4. **Audit keamanan sebelum rilis** — cek sistematis sebelum tag versi/rilis resmi: apakah
   ada secret ter-commit (API key, password), apakah ada celah dikenal (SSRF, path
   traversal, dll). WAJIB dilakukan sebelum deploy ke hosting publik (Minggu 3) dan sebelum
   setiap tag versi resmi ke depan.

5. **Pemisahan `docs/` vs `notes/`** — `docs/` untuk dokumentasi formal stabil (arsitektur,
   cara install, panduan pengguna). `notes/` untuk catatan kerja yang sering berubah (status
   progress, keputusan yang baru diambil, TODO). Terapkan pemisahan ini di struktur folder
   `dss-umkm-ciwidey/docs/` — pertimbangkan tambah `notes/` terpisah kalau belum ada.

6. **Fail-fast di level aplikasi** — aplikasi harus MENOLAK start kalau konfigurasi penting
   hilang/salah, bukan diam-diam jalan dengan konfigurasi salah lalu gagal di tengah jalan
   dengan cara membingungkan. Terapkan ini saat menangani T-8 (dependency hilang harus
   memunculkan error jelas saat startup, bukan gagal senyap saat load model di tengah
   pemakaian) dan config sensitif lain (API key Open-Meteo kalau ada, koneksi DB, dll).

7. **Optimasi dependency (hapus yang tidak terpakai)** — audit dependency secara berkala,
   jangan biarkan dependency mati menumpuk. Terapkan saat kerjakan T-8: HANYA masukkan paket
   yang benar-benar dipakai (sudah dilakukan dengan benar — prophet/statsmodels/optuna
   dikeluarkan karena terverifikasi tidak dipakai runtime `app/`). Audit ulang tiap kali ada
   perubahan besar ke kode.

8. **Version control yang rapi** — tag semantic (contoh: `v1.0.0`), commit message jelas dan
   deskriptif (bukan "update" atau "fix"), hindari commit yang tidak jelas maksudnya. Sudah
   diterapkan sejauh ini (commit README, commit requirements.txt) — pertahankan pola ini
   untuk SETIAP commit ke depan tanpa kecuali.

## Struktur folder lokal (referensi baca-saja, sudah terverifikasi)

```
C:\Users\Arif\dss-umkm-project\
├── CLAUDE.md                          (file ini)
├── brief\BRIEF-PROYEK-DSS-UMKM-v2.md  sumber kebenaran lengkap — update di sini kalau ada
│                                       keputusan baru, temuan baru, atau progres besar
├── repo\
│   ├── dss-umkm\                      77 file, aplikasi Streamlit, git clean
│   ├── dss-model\                     59 file, training & serialisasi model, git clean
│   └── generasi-dataset-umkm\         4 file, generator dataset sintetis, git clean
└── docs\                              dokumentasi teknis & panduan pengguna (diisi Minggu 4)
```

Ini adalah repo Felix asli (tiga repo terpisah), dipertahankan sebagai referensi baca-saja
karena jadi Lampiran B skripsi — jangan diubah isinya.

## Repo baru untuk perbaikan aktif — digabung, bukan pisah

Keputusan (lihat brief Bagian 4b untuk alasan lengkap): repo lama Felix tetap tiga dan tidak
diubah, tapi pekerjaan perbaikan aktif dilakukan di **satu repo baru gabungan**:

```
dss-umkm-ciwidey/          (nama baru, publik, milik Arif)
├── app/                   (isi dss-umkm)
├── model/                 (isi dss-model)
├── dataset-gen/            (isi generasi-dataset-umkm)
├── docs/                  dokumentasi stabil — arsitektur, cara install (diisi Minggu 4)
├── notes/                 catatan kerja yang sering berubah — status, keputusan
├── evidence/              snapshot bukti sebelum/sesudah, write-once, immutable,
│                          diberi nama tanggal (misal 2026-09-04-sebelum-perbaikan/)
├── README.md              (wajib jelaskan riwayat: melanjutkan skripsi Felix, link 3 repo asli)
└── CLAUDE.md
```

Alasan gabung: skala kecil (140 file total), ketiganya satu pipeline (generate→train→serve,
dibuktikan hash CSV identik antar-repo), pemisahan lama sudah terbukti menyebabkan drift
(T-14, T-17, T-18), dan deployment jauh lebih praktis dari satu repo.

## Kalau brief ini dan brief di Claude.ai Project berbeda

`brief/BRIEF-PROYEK-DSS-UMKM-v2.md` di folder ini **harus** jadi salinan terbaru dari yang ada
di Claude.ai Project "DSS UMKM Alamendah — Deployment & Pengabdian Masyarakat". Kalau ada
perubahan besar di salah satu sisi (keputusan baru dari dosen, temuan bug baru, progres
milestone), Arif yang bertanggung jawab menyalin perubahan itu ke kedua tempat — beri tahu Arif
kalau kamu curiga ada versi yang lebih baru di sisi lain.
