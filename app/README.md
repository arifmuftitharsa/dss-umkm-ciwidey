# DSS UMKM — Web App (Prototipe)

Prototipe Decision Support System manajemen stok untuk pemilik UMKM sektor
wisata. Studi kasus: UMKM Olahan Stroberi, Desa Wisata Alamendah, Ciwidey.

Repo pendamping: **dss-model** (pipeline pemodelan & evaluasi Bab III–IV).

## Cara menjalankan
```bash
pip install -r requirements.txt
streamlit run app.py
```
Folder `.streamlit/` berisi tema aplikasi, pastikan ikut ter-extract.

## Alur sistem
```
riwayat penjualan ─┐
kalender libur ────┼─> fitur ─> XGBoost ─> forecast produk
prakiraan cuaca ───┘                            │
                                          BOM  ─┴─> kebutuhan bahan baku
                                                      │
                                          EOQ/ROP ────┴─> beli apa, berapa, kapan
```

## Struktur folder
```
dss-umkm/
├── app.py                  # entry point: tema, sidebar, navigasi antar halaman
├── config.py               # parameter domain default (produk, bahan baku, BOM, Z)
├── .streamlit/config.toml  # tema tampilan Streamlit
│
├── core/                   # logika sistem (tanpa tampilan)
│   ├── features.py         # bangun 20 fitur saat inference (harus = saat training)
│   ├── forecasting.py      # muat model .joblib + forecast rekursif n hari
│   └── inventory.py        # forecast -> BOM -> EOQ / ROP / safety stock
│
├── data/                   # sumber & penyimpanan data
│   ├── weather.py          # cuaca (Open-Meteo 1-16 hari, sisanya klimatologi) + libur
│   ├── store.py            # database SQLite (produk, bahan baku, BOM, window libur)
│   ├── synthetic.py        # generator dataset sintetis (Sec. 3.2.2)
│   ├── generate_historis.py# riwayat sintetis untuk produk yang baru ditambah
│   ├── record_sales.py     # pencatatan penjualan harian oleh pemilik
│   ├── historis_penjualan.csv
│   └── dss_umkm.db
│
├── views/                  # satu file = satu halaman
│   ├── overview.py         # Ringkasan Operasional
│   ├── forecasting.py      # Perkiraan Penjualan (7/14/30 hari)
│   ├── inventory.py        # Stok & Pembelian
│   ├── pengaturan.py       # Manajemen & Pengaturan (5 tab)
│   └── research.py         # TIDAK DI INCLUDE DI FINAL WEB (KARENA INI HANYA VISUAL TEKNIS)
│
├── components/
│   ├── ui.py               # tema CSS + komponen kartu/KPI/action
│   └── charts.py           # grafik Plotly
│
└── models_trained/         # ARTEFAK DARI REPO dss-model — jangan diedit manual
    ├── xgb_P001.joblib     # Pipeline(StandardScaler + XGBRegressor) per produk
    ├── xgb_P002.joblib
    ├── xgb_P003.joblib
    ├── meta.json           # daftar 20 kolom fitur + hyperparameter terpilih
    └── akurasi_horizon.json# akurasi backtest H+7 / H+14 / H+30
```

## Sinkronisasi model dengan repo dss-model
Model di `models_trained/` **bukan** dilatih di repo ini. Setelah melatih ulang
di repo `dss-model`:

```bash
# di repo dss-model
python serialize_models.py
python backtest_horizon.py
# lalu salin SELURUH isi folder ini ke dss-umkm/models_trained/
```

Salin semuanya sekaligus (model + `meta.json` + `akurasi_horizon.json`). Jika
hanya sebagian yang disalin, daftar fitur model bisa tidak cocok dengan
`core/features.py` dan aplikasi akan berhenti dengan pesan
`Model xgb_P00X.joblib dilatih dengan N fitur, sedangkan sistem mengirim M fitur`.

## Normalisasi
`.joblib` berisi `Pipeline(StandardScaler + XGBRegressor)`, jadi `core/features.py`
mengirim fitur MENTAH dan scaling terjadi otomatis di dalam pipeline memakai
scaler yang di-fit saat pelatihan. Jangan men-scale manual di sisi app.

## Catatan
- Aplikasi single-user, dijalankan lokal, tanpa login (Sec. 3.7.1).
- Satu-satunya layanan eksternal adalah Open-Meteo. Bila offline, sistem tetap
  jalan memakai klimatologi curah hujan bulanan.
- Produk, bahan baku, stok, BOM, dan window libur dibaca dari SQLite dan dapat
  diubah pemilik lewat halaman Manajemen; `config.py` hanya nilai awal.
