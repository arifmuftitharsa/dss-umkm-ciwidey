# DSS UMKM Ciwidey

Sistem pendukung keputusan berbasis machine learning untuk prediksi kebutuhan stok bahan baku
UMKM olahan stroberi di Desa Wisata Alamendah, Ciwidey, Bandung Selatan. Proyek ini melanjutkan
skripsi Felix Joshua Paulus (105222032), "Pembangunan Model Prediksi Kebutuhan Stok Bahan Baku
UMKM Berbasis Machine Learning", Program Studi Ilmu Komputer, Universitas Pertamina. Pekerjaan
lanjutan oleh Arif mencakup perbaikan kode, deployment, dokumentasi, dan onboarding pengguna,
sebagai bagian dari kegiatan pengabdian masyarakat di Ciwidey.

## Riwayat dan Atribusi

Repo ini awalnya tiga repo terpisah milik Felix Joshua Paulus, digabung menjadi satu repo untuk
pekerjaan lanjutan. Alasan penggabungan:

1. Skalanya kecil — total 140 file (77 + 59 + 4). Tidak butuh isolasi repo untuk performa
   maupun siklus rilis independen.
2. Ketiganya sebenarnya satu pipeline (generate → train → serve), bukan tiga proyek independen —
   dibuktikan langsung oleh temuan sendiri: hash CSV `dss-model` dan `generasi-dataset-umkm`
   identik byte-per-byte.
3. Pemisahan repo lama justru menyebabkan drift yang sudah terbukti terjadi (lihat temuan T-14,
   T-17, T-18 di brief proyek): versi pustaka beda antar-repo, output evaluasi tak sinkron dengan
   kode terbaru, dan tidak ada mekanisme otomatis yang memberi tahu kalau sudah tidak cocok.
4. Untuk deployment, satu repo jauh lebih praktis — CI/CD dan Docker build tidak perlu clone tiga
   sumber terpisah.

Repo asli (arsip, Lampiran B skripsi):

- Kode Prototipe: https://github.com/felixjoshua/dss-umkm
- Kode Model: https://github.com/felixjoshua/dss-model
- Kode Dataset: https://github.com/felixjoshua/generasi-dataset-umkm

Repo asli di atas tetap dipertahankan sebagai referensi dan lampiran skripsi, tidak diubah.

## Struktur Folder

```
dss-umkm-ciwidey/
├── app/           aplikasi Streamlit (dari dss-umkm)
├── model/         training & serialisasi model (dari dss-model)
├── dataset-gen/   generator dataset sintetis (dari generasi-dataset-umkm)
├── docs/          dokumentasi teknis & panduan pengguna (kosong, diisi bertahap)
└── CLAUDE.md      konteks kerja untuk sesi Claude berikutnya
```

## Status Pengerjaan

Audit kode menemukan sejumlah temuan (T-1 sampai T-18) yang mencakup beberapa masalah kritis
yang perlu diperbaiki sebelum deployment ke pengguna nyata. Detail teknis tiap temuan, tingkat
prioritas, dan rencana kerja perbaikan tidak diulang di sini — lihat dokumen brief proyek untuk
rincian lengkap. Repo ini belum pernah di-deploy secara daring.

## Cara Menjalankan (Development Lokal)

```bash
git clone https://github.com/arifmuftitharsa/dss-umkm-ciwidey.git
cd dss-umkm-ciwidey
python -m venv venv
```

Aktifkan virtual environment (`venv\Scripts\activate` di Windows, `source venv/bin/activate`
di Linux/Mac), lalu install requirements sesuai folder yang mau dijalankan.

**Aplikasi Streamlit (`app/`):**

```bash
cd app
pip install -r requirements.txt
streamlit run app.py
```

**Peringatan:** `app/requirements.txt` diketahui belum lengkap (lihat temuan T-8 di brief) —
hilang `xgboost`, `joblib`, `holidays`, `requests`, dan `scikit-learn` padahal di-import
langsung oleh kode. Perintah `pip install -r requirements.txt` di atas belum tentu cukup untuk
menjalankan aplikasi tanpa error sampai berkas ini ditambal.

**Training ulang model (`model/`):**

```bash
cd model
pip install -r requirements.txt
python run_pipeline.py
```

**Generate ulang dataset sintetis (`dataset-gen/`):**

```bash
cd dataset-gen
pip install -r requirementsumkm.txt
python generate_dataset.py
```

Catatan: nama berkasnya `requirementsumkm.txt`, bukan `requirements.txt` (lihat temuan T-17 di
brief).

## Lisensi dan Kontak

TBD.
