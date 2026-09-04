"""
benchmark_inference.py - Waktu inference XGBoost vs Hybrid Prophet-XGBoost.

Dasar pemilihan XGBoost di Bab IV: akurasi setara hybrid (selisih MAPE ~0,06%)
tetapi jauh lebih ringan saat inference - fase yang dijalankan tiap kali pemilik
UMKM meminta forecast di dashboard.

Jalankan:  python benchmark_inference.py
Output  :  outputs/benchmark_inference.csv
"""
import warnings
import time
import json

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from prophet import Prophet

import config
from feature_engineering import (load_product_series, build_features,
                                 get_feature_columns, temporal_split, scale_features)

N_REPEAT = 100  # diulang 100x lalu dirata-rata agar tidak terpengaruh fluktuasi


def benchmark_product(pid, df_all, fcols, meta):
    """Ukur waktu inference kedua model untuk satu produk. -> dict"""
    params = meta["products"][pid]["best_params"]

    df = build_features(load_product_series(df_all, pid)).dropna().reset_index(drop=True)
    tr, va, te = temporal_split(df)
    # Normalisasi (Sec. 3.3.4), sama seperti run_pipeline.py
    trs, vas, tes, _ = scale_features(tr.copy(), va.copy(), te.copy(), fcols)

    # XGBoost tunggal
    xgb = XGBRegressor(objective="reg:squarederror", random_state=config.RANDOM_SEED,
                       early_stopping_rounds=50, eval_metric="rmse", **params)
    xgb.fit(trs[fcols], trs["qty_sold"],
            eval_set=[(vas[fcols], vas["qty_sold"])], verbose=False)

    # Hybrid: Prophet (pola umum) + XGBoost (residual)
    dp = tr[["date", "qty_sold"]].rename(columns={"date": "ds", "qty_sold": "y"})
    prophet = Prophet(weekly_seasonality=True, yearly_seasonality=True,
                      daily_seasonality=False)
    prophet.fit(dp)
    resid = tr["qty_sold"].values - prophet.predict(
        tr[["date"]].rename(columns={"date": "ds"}))["yhat"].values
    res_tr = trs.copy()
    res_tr["resid"] = resid
    xgb_h = XGBRegressor(objective="reg:squarederror",
                         random_state=config.RANDOM_SEED, **params)
    xgb_h.fit(res_tr[fcols], res_tr["resid"])

    te_ds = te[["date"]].rename(columns={"date": "ds"})

    t0 = time.perf_counter()
    for _ in range(N_REPEAT):
        _ = xgb.predict(tes[fcols])
    t_xgb = (time.perf_counter() - t0) / N_REPEAT * 1000  # ms

    t0 = time.perf_counter()
    for _ in range(N_REPEAT):
        _ = prophet.predict(te_ds)["yhat"].values + xgb_h.predict(tes[fcols])
    t_hyb = (time.perf_counter() - t0) / N_REPEAT * 1000  # ms

    return {
        "product": pid,
        "product_name": config.PRODUCT_NAMES[pid],
        "n_test_rows": len(tes),
        "n_repeat": N_REPEAT,
        "xgboost_ms": round(t_xgb, 2),
        "hybrid_ms": round(t_hyb, 2),
        "hybrid_lebih_lambat_x": round(t_hyb / t_xgb, 1),
    }


def main():
    df_all = pd.read_csv(config.DATA_PATH)
    fcols = get_feature_columns("full")
    meta = json.load(open("models_trained/meta.json"))

    rows = []
    for pid in config.PRODUCTS:                    # ketiga produk, bukan satu
        print(f"> Benchmark {pid} ({config.PRODUCT_NAMES[pid]}) ...", flush=True)
        rows.append(benchmark_product(pid, df_all, fcols, meta))

    res = pd.DataFrame(rows)

    # baris rata-rata lintas produk
    avg = {
        "product": "RATA-RATA", "product_name": "-",
        "n_test_rows": int(res.n_test_rows.mean()), "n_repeat": N_REPEAT,
        "xgboost_ms": round(res.xgboost_ms.mean(), 2),
        "hybrid_ms": round(res.hybrid_ms.mean(), 2),
        "hybrid_lebih_lambat_x": round(res.hybrid_ms.mean() / res.xgboost_ms.mean(), 1),
    }
    res = pd.concat([res, pd.DataFrame([avg])], ignore_index=True)

    out = config.OUTPUT_DIR / "benchmark_inference.csv"
    res.to_csv(out, index=False)

    print(f"\nWaktu inference (rata-rata {N_REPEAT}x per produk):")
    print(res.to_string(index=False))
    print(f"\nDisimpan ke {out}")


if __name__ == "__main__":
    main()
