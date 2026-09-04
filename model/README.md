# DSS Model — Pipeline Pemodelan & Evaluasi

Kode eksperimen pemodelan, terpisah dari web app. Mengimplementasikan Bab III
dan menghasilkan angka-angka Bab IV.

Repo pendamping: **dss-umkm** (web app Streamlit).

## Struktur
```
config.py               # parameter global (produk, BOM, split, horizon, seed)
feature_engineering.py  # lag/rolling/encoding, scaling, split 70/15/15 (Sec. 3.3)
evaluate.py             # metrik MAE / RMSE / MAPE (Sec. 3.6.1)
inventory.py            # BOM, EOQ/ROP/safety stock, simulasi A vs B (Sec. 3.6.3-3.6.5)
models/
  model_arima.py        # ARIMA / ARIMAX
  model_prophet.py      # Prophet + regressor cuaca + holiday
  model_xgboost.py      # XGBoost + tuning Optuna
  model_hybrid.py       # Hybrid Prophet-XGBoost (residual learning)
run_pipeline.py         # orchestrator utama
baseline_naif.py        # baseline naive / seasonal naive / moving average
backtest_horizon.py     # akurasi recursive H+7 / H+14 / H+30
benchmark_inference.py  # waktu inference XGBoost vs Hybrid (3 produk)
serialize_models.py     # simpan model terpilih ke models_trained/
data_sintetis_permintaan.csv
```
Jalankan dari folder root repo ini, bukan dari dalam `models/`.

## Cara menjalankan
```bash
pip install -r requirements.txt
python run_pipeline.py          # hasil utama Bab IV (10-20 menit)
python baseline_naif.py         # baseline pembanding
python backtest_horizon.py      # akurasi multi-horizon
python benchmark_inference.py   # waktu inference XGBoost vs Hybrid
python serialize_models.py      # latih & simpan model untuk web app
```

## Output -> tabel di laporan
| File                                | Dipakai di |
|-------------------------------------|-----------|
| `outputs/hasil_baseline_naif.csv`   | Tabel 4.14 Baseline sederhana |
| `outputs/hasil_komparatif_model.csv`| Tabel 4.15-4.16 Perbandingan model |
| `outputs/hasil_ablation_study.csv`  | Tabel 4.21 Ablation study |
| `outputs/benchmark_inference.csv`   | Justifikasi pemilihan XGBoost (Sec. 4.4) |
| `outputs/rekomendasi_inventori.csv` | Sec. 4.7 EOQ/ROP per bahan |
| `outputs/simulasi_inventori.csv`    | Tabel 4.23 Skenario A vs B |
| `models_trained/akurasi_horizon.json` | Tabel 4.22 Multi-horizon |
| `models_trained/meta.json`          | Lampiran (fitur & hyperparameter) |

## Normalisasi (Sec. 3.3.4)
`scale_features()` di `feature_engineering.py` dipanggil pada `run_pipeline.py`
(evaluasi model + ablation) dan `serialize_models.py` (model final). Scaler
di-fit hanya pada data train, val/test hanya di-transform.

Pada `serialize_models.py`, scaler dan model dibungkus jadi satu
`sklearn.pipeline.Pipeline` sebelum disimpan ke `.joblib`, sehingga saat
inference cukup memanggil `predict()` dengan fitur mentah — scaling dilakukan
otomatis memakai scaler yang sama seperti saat pelatihan.

Catatan: XGBoost berbasis pohon sehingga invariant terhadap skala; normalisasi
tidak mengubah nilai prediksi (terverifikasi: selisih MAPE 0,0000). Langkah ini
disertakan agar pipeline konsisten dengan metodologi Sec. 3.3.4.

## Setelah melatih ulang model
`models_trained/` adalah sumber tunggal artefak model. Setelah menjalankan
`serialize_models.py` dan `backtest_horizon.py`, salin **seluruh** isinya ke
`dss-umkm/models_trained/` agar web app memakai model yang sama.

## Catatan
- File di `models/` adalah library, dipanggil `run_pipeline.py`, bukan skrip mandiri.
- Seed acak diatur di `config.RANDOM_SEED` agar hasil reprodusibel.
