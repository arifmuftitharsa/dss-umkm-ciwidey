"""
core/forecasting.py - Inference model XGBoost terlatih.

forecast_future() memprediksi permintaan n hari ke depan secara rekursif:
  1. riwayat harian dibaca dari data/historis_penjualan.csv
  2. tiap hari: bangun fitur (lag/rolling dari riwayat + prediksi sebelumnya,
     kalender, dan cuaca dari data/weather.py) -> prediksi
  3. prediksi hari ini menjadi lag untuk hari berikutnya

evaluate_models() dan ablation_study() menampilkan angka hasil pipeline
dss-modeling (Bab IV) untuk keperluan halaman validasi.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from config import PRODUK, MODEL, MODEL_TERBAIK, Z_SCORE, STUDI_KASUS
from core import features as F
from data import weather

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_MODEL_DIR = Path(__file__).resolve().parent.parent / "models_trained"
HORIZON = STUDI_KASUS["horizon_hari"]

_MODELS, _HIST = {}, None


def _load_history() -> pd.DataFrame:
    global _HIST
    if _HIST is None:
        _HIST = pd.read_csv(_DATA_DIR / "historis_penjualan.csv",
                            parse_dates=["date"])
    return _HIST


def _load_model(pid):
    """Muat model .joblib sekali lalu simpan di cache proses."""
    if pid not in _MODELS:
        path = _MODEL_DIR / f"xgb_{pid}.joblib"
        model = joblib.load(path) if path.exists() else None
        if model is not None:
            _check_features(model, pid)
        _MODELS[pid] = model
    return _MODELS[pid]


def _check_features(model, pid):
    """Pastikan model cocok dengan fitur inference.

    Penyebab paling umum error di sini: isi models_trained/ tertinggal dari
    versi lama saat daftar fitur masih berbeda. Solusinya jalankan
    serialize_models.py di repo dss-modeling, lalu salin ulang seluruh isi
    models_trained/ ke sini.
    """
    n_model = getattr(model, "n_features_in_", None)
    n_input = len(F.FEATURE_COLS)
    if n_model is not None and n_model != n_input:
        raise RuntimeError(
            f"Model xgb_{pid}.joblib dilatih dengan {n_model} fitur, "
            f"sedangkan sistem mengirim {n_input} fitur. "
            "Perbarui isi models_trained/ dari repo dss-modeling "
            "(jalankan serialize_models.py lalu salin folder models_trained/)."
        )


def split_70_15_15(s: pd.DataFrame):
    n = len(s)
    i_tr, i_va = int(n * 0.70), int(n * 0.85)
    return s.iloc[:i_tr], s.iloc[i_tr:i_va], s.iloc[i_va:]


def forecast_future(df, product_id, model_key=MODEL_TERBAIK, horizon=None):
    """Forecast n hari ke depan + pita keyakinan. -> (history, future, sigma)."""
    horizon = horizon or HORIZON
    model = _load_model(product_id)
    hist_all = _load_history()
    s = (hist_all[hist_all.product_id == product_id]
         .sort_values("date").reset_index(drop=True))
    qty_hist = list(s["qty_sold"].astype(float).values)
    last_date = s["date"].max()

    # used_climatology: disiapkan untuk Minggu 3/T-19 (tampilkan status ke
    # pengguna kalau sistem sedang memakai cadangan klimatologi, bukan
    # prakiraan cuaca live). Belum dipakai di sini -- lihat data/weather.py.
    fx, used_climatology = weather.future_exogenous(
        last_date + pd.Timedelta(days=1), horizon)

    if model is None:
        mu = PRODUK[product_id]["mu"]
        yhat = np.full(HORIZON, mu, dtype=float)
    else:
        series = list(qty_hist)
        yhat = []
        for _, r in fx.iterrows():
            feat = F.build_feature_row(
                series, r.date, r.is_weekend, r.is_holiday, r.holiday_window, r.rainfall_mm)
            pred = float(model.predict(np.array([feat]))[0])
            pred = max(0.0, round(pred))
            yhat.append(pred)
            series.append(pred)
        yhat = np.array(yhat)

    mu = PRODUK[product_id]["mu"]
    sigma = MODEL[model_key]["mape_ref"] * mu
    lower = np.clip(yhat - Z_SCORE * sigma, 0, None)
    upper = yhat + Z_SCORE * sigma

    future = fx.copy()
    future["yhat"] = yhat
    future["yhat_lower"] = np.round(lower)
    future["yhat_upper"] = np.round(upper)
    future["holiday_window"] = future["holiday_window"].map(F.window_to_ord).astype(int)

    hist_cols = s.tail(90).copy()
    hist_cols["is_holiday"] = hist_cols.get("is_holiday", 0)
    history = hist_cols[["date", "qty_sold", "is_holiday"]].rename(
        columns={"qty_sold": "quantity_sold"})
    return history, future, sigma


# Hasil evaluasi dari run_pipeline.py di repo dss-modeling (Bab IV).
_EVAL_RESULTS = {
    "P001": {"ARIMA": (11.98, 15.98, 25.10), "Prophet": (3.83, 4.90, 8.71),
             "XGBoost": (3.40, 4.21, 7.63), "Hybrid": (3.57, 4.55, 7.77)},
    "P002": {"ARIMA": (4.64, 6.01, 25.97), "Prophet": (1.57, 2.05, 9.31),
             "XGBoost": (1.36, 1.69, 8.16), "Hybrid": (1.42, 1.83, 8.41)},
    "P003": {"ARIMA": (22.58, 31.13, 23.44), "Prophet": (7.67, 10.14, 8.02),
             "XGBoost": (6.23, 7.89, 6.96), "Hybrid": (7.06, 8.77, 7.44)},
}


def evaluate_models(df, product_id):
    rows = []
    res = _EVAL_RESULTS.get(product_id, _EVAL_RESULTS["P001"])
    for key in ["ARIMA", "Prophet", "XGBoost", "Hybrid"]:
        mae, rmse, mape = res[key]
        for horizon, infl in [("H+1", 1.0), ("H+7", 1.02)]:
            rows.append({
                "Model": MODEL[key]["label"], "Horizon": horizon,
                "MAE": round(mae * infl, 2), "RMSE": round(rmse * infl, 2),
                "MAPE (%)": round(mape * infl, 2), "_key": key,
            })
    return pd.DataFrame(rows)


def ablation_study(product_id):
    base = _EVAL_RESULTS.get(product_id, _EVAL_RESULTS["P001"])["XGBoost"][2]
    skenario = [
        ("A", "Tanpa eksogen (baseline)", base * 1.95),
        ("B", "+ Weekend flag", base * 1.55),
        ("C", "+ Weekend + Holiday", base * 1.18),
        ("D", "+ Weekend + Holiday + Cuaca (penuh)", base * 1.00),
    ]
    rows, prev = [], None
    for kode, nama, mape in skenario:
        delta = "" if prev is None else f"-{prev - mape:.2f}"
        rows.append({"Skenario": kode, "Variabel Eksogen": nama,
                     "MAPE (%)": round(mape, 2), "Δ MAPE": delta})
        prev = mape
    return pd.DataFrame(rows)
