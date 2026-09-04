"""
core/forecasting.py - Inference model XGBoost terlatih.

forecast_future() memprediksi permintaan n hari ke depan secara rekursif:
  1. riwayat harian dibaca dari data/historis_penjualan.csv
  2. tiap hari: bangun fitur (lag/rolling dari riwayat + prediksi sebelumnya,
     kalender, dan cuaca dari data/weather.py) -> prediksi
  3. prediksi hari ini menjadi lag untuk hari berikutnya
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from config import MODEL, MODEL_TERBAIK, Z_SCORE, STUDI_KASUS
from core import features as F
from data import store
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

    # T-4: daftar produk dari database (store.get_produk_dict()), bukan
    # config.PRODUK statis -- produk baru yang ditambah lewat dashboard
    # harus bisa diforecast tanpa KeyError. Diambil sekali di sini, dipakai
    # ulang di bawah (hindari query DB berulang dalam satu panggilan).
    produk = store.get_produk_dict()
    if product_id not in produk:
        raise ValueError(
            f"Produk '{product_id}' tidak ditemukan di database. "
            "Pastikan produk sudah disimpan lewat halaman Manajemen "
            "sebelum diminta forecast-nya."
        )
    mu = produk[product_id]["mu"]

    model = _load_model(product_id)
    hist_all = _load_history()
    s = (hist_all[hist_all.product_id == product_id]
         .sort_values("date").reset_index(drop=True))

    # Titik reset operasional (T-1): begitu diaktifkan, riwayat dipotong ke
    # baris date >= mulai_operasional -- memutus rantai posisional lag/rolling
    # dari data training sintetis lama (lihat data/record_sales.py). Sebelum
    # diaktifkan, perilaku sama seperti sekarang (pakai seluruh riwayat).
    mulai_operasional = store.get_tanggal_mulai_operasional()
    if mulai_operasional is not None:
        s = s[s.date >= mulai_operasional].reset_index(drop=True)

    if s.empty:
        # Produk tanpa riwayat SAMA SEKALI (T-4: baru ditambah lewat
        # dashboard, belum pernah dicatat sekali pun) -- beda dari
        # cold-start pasca-reset T-1 (yang selalu punya mulai_operasional
        # sebagai titik acuan). Tanpa fallback ini, last_date jadi NaT dan
        # weather.future_exogenous(NaT, ...) crash. Forecast produk baru
        # paling masuk akal mulai dari hari ini sungguhan.
        last_date = pd.Timestamp.now().normalize() - pd.Timedelta(days=1)
    else:
        last_date = s["date"].max()

    qty_hist = list(s["qty_sold"].astype(float).values)

    # used_climatology: disiapkan untuk Minggu 3/T-19 (tampilkan status ke
    # pengguna kalau sistem sedang memakai cadangan klimatologi, bukan
    # prakiraan cuaca live). Belum dipakai di sini -- lihat data/weather.py.
    fx, used_climatology = weather.future_exogenous(
        last_date + pd.Timedelta(days=1), horizon)

    if model is None or len(qty_hist) == 0:
        # len(qty_hist) == 0: baru saja reset operasional, belum ada satu
        # pun catatan asli -- build_feature_row() butuh minimal 1 elemen
        # (s[0] dipakai saat riwayat lebih pendek dari lag/window). Pakai
        # base demand datar sampai hari pertama tercatat, sama seperti
        # jalur "model belum tersedia" yang sudah ada. Produk baru tanpa
        # model .joblib juga otomatis lewat sini -- mu berasal dari input
        # pemilik sendiri saat menambah produk (T-4), bukan karangan sistem.
        #
        # horizon (bukan HORIZON konstanta global) -- bug T-4 lama: panjang
        # array dulu selalu 7 walau horizon diminta 14/30.
        yhat = np.full(horizon, mu, dtype=float)
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
