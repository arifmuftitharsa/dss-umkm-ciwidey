# CLAUDE.md — DSS UMKM Alamendah

Ini proyek pengabdian masyarakat/skripsi kakak tingkat (Felix Joshua Paulus, 105222032) yang
sedang dilanjutkan oleh Arif: perbaikan kode, deployment, dokumentasi, onboarding pengguna.

**Sumber kebenaran lengkap ada di `brief/BRIEF-PROYEK-DSS-UMKM-v2.md` di folder ini — baca file
itu dulu sebelum menjawab pertanyaan substantif soal skripsi, temuan bug, atau rencana kerja.**
File ini (`CLAUDE.md`) hanya ringkasan supaya kamu tidak mulai dari nol tiap sesi.

## Ringkasan super singkat

Sistem: Streamlit + SQLite + XGBoost, prediksi kebutuhan stok bahan baku UMKM olahan stroberi
(Ciwidey). Skripsi sumber pakai data 100% sintetis. Prototipe belum pernah deploy daring.

## 15 temuan (T-1 s.d. T-15) — status per direktori

Detail penuh tiap temuan ada di brief. Ringkasan cepat:

| # | Temuan | Prioritas |
|---|--------|-----------|
| T-1 | `data/record_sales.py` kunci tanggal di 2025-12-31, tolak lompatan | KRITIS — blocker demo |
| T-2 | `core/forecasting.py` tambah noise acak ke prediksi (kosmetik) | KRITIS — hapus 2 baris |
| T-3 | Sigma/safety stock dari konstanta literatur, bukan error model nyata | TINGGI — akar stockout |
| T-4 | Produk baru via dashboard: KeyError, tidak masuk hitungan bahan | KRITIS |
| T-5 | GUGUR — scaler aman, sudah dibungkus Pipeline di `.joblib` | selesai, tidak perlu kerja |
| T-6 | GUGUR — CSV vs SQLite bukan konflik sumber, pembagian sudah benar | selesai |
| T-7 | GUGUR — fallback cuaca luring sudah ada dan bagus | selesai (T-7b masih ada, lihat bawah) |
| T-7b | Bug penyelarasan tanggal cuaca saat forecast_future | KECIL, ikut selesai bareng T-1 |
| T-8 | `requirements.txt` hilang xgboost/joblib/holidays/requests/scikit-learn | TINGGI — blocker deploy |
| T-9 | Tanpa autentikasi, storage ephemeral (data hilang saat redeploy) | SEDANG-BESAR |
| T-10 | Angka evaluasi palsu di kode (`_EVAL_RESULTS`, `simulasi_skenario`) — kode mati, tak tampil, tapi repo publik | MENENGAH — hapus saja |
| T-11 | `config.py` beda dari skripsi (harga, BOM, kode bahan) | MENENGAH — akan diganti data mitra asli |
| T-12 | Batas lot EOQ (Persamaan 3.11) tidak diimplementasikan, `shelf_life` tidak ada | SEDANG — bareng T-3 jadi akar stockout |
| T-13 | Startup regenerasi dataset sintetis 3 tahun, tidak dipakai (`forecast_future` baca CSV, bukan df) | RENDAH |
| T-14 | Output `dss-model` masih ARIMA (32%), skripsi laporkan ARIMAX (8-9%) — perlu run_pipeline.py ulang | RENDAH |
| T-15 | Model dilatih 100% data sintetis — jangan sebut akurasi ke UMKM | selalu berlaku |
| T-16 | Formula demand di `generate_dataset.py` multiplicative, skripsi Pers. 3.1 tulis aditif — beda struktur matematis | RENDAH, akademis saja |
| T-17 | `holidays==0.98` di repo vs 0.101 diverifikasi skripsi; nama file `requirementsumkm.txt` bukan `requirements.txt` | RENDAH |
| T-18 | Repo tak 100% reproduksi Tabel 4.7 (demand P001) walau seed=42 sama — kode direvisi setelah tabel final skripsi dibuat | RENDAH, jangan asumsikan retraining = angka skripsi identik |

## Aturan kerja (sama seperti project Claude.ai)

1. Jangan mengarang isi kode. Baca berkas asli sebelum menyimpulkan.
2. Benar sebelum indah — jangan poles UI sebelum T-1/T-2 (blocker demo) beres.
3. Semua teks yang dilihat pengguna akhir: Bahasa Indonesia sehari-hari, tanpa jargon.
4. Jangan sebut angka akurasi model (92%, MAPE) ke pelaku UMKM di lapangan.
5. Debugging/edit kode yang sudah jalan → full file rewrite siap pakai, bukan snippet.
6. Belajar konsep baru dari nol → guided learning, logika dulu.
7. Perubahan besar butuh bukti sebelum-sesudah (screenshot atau angka) untuk laporan.
8. Kalibrasi inventori (T-3, T-12), skala tenant, dan status akademis pekerjaan ini —
   **belum final diputuskan** (lihat Bagian 6 brief). Tanya Arif dulu kalau kerjaan bergantung
   pada ini, jangan asumsikan sudah selesai.

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
├── docs/
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
