"""
backtest_horizon.py - Akurasi forecast recursive per horizon (H+7/14/30).

Rolling-origin backtest pada test set, meniru perilaku deployment: prediksi
hari sebelumnya dipakai sebagai lag hari berikutnya, eksogen memakai nilai
aktual.

Output: models_trained/akurasi_horizon.json (dipakai dashboard).
"""
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

import config
import feature_engineering as fe
import evaluate as ev

warnings.filterwarnings("ignore")

HW_ONEHOT = {"H-1": "hw_hm1", "H": "hw_h0", "H+1": "hw_hp1", "H+2": "hw_hp2"}
HW_COLS = ["hw_hm1", "hw_h0", "hw_hp1", "hw_hp2"]
MODEL_DIR = Path(__file__).resolve().parent / "models_trained"
HORIZONS = [7, 14, 30]


def recursive_forecast(model, hist_series, exog_rows, feats):
    """Forecast len(exog_rows) hari recursive. exog_rows: list dict eksogen."""
    series = list(hist_series)
    preds = []
    for ex in exog_rows:
        row = {}
        for lag in fe.config.LAG_FEATURES:
            row[f"lag_{lag}"] = series[-lag] if len(series) >= lag else series[0]
        for w in fe.config.ROLLING_WINDOWS:
            win = series[-w:] if len(series) >= w else series
            row[f"roll_mean_{w}"] = float(np.mean(win))
        win7 = series[-7:] if len(series) >= 7 else series
        row["roll_std_7"] = float(np.std(win7, ddof=1)) if len(win7) > 1 else 0.0
        dow = pd.Timestamp(ex["date"]).dayofweek
        for i, name in enumerate(fe.DOW_NAMES):
            row[name] = 1 if dow == i else 0
        row["is_weekend"] = ex["is_weekend"]
        row["is_holiday"] = ex["is_holiday"]
        for c in HW_COLS:
            row[c] = ex[c]
        row["rainfall_mm"] = ex["rainfall_mm"]
        x = np.array([[row[c] for c in feats]])
        p = max(0.0, float(model.predict(x)[0]))
        preds.append(p)
        series.append(p)
    return np.array(preds)


def main():
    df_all = pd.read_csv(config.DATA_PATH)
    feats = fe.get_feature_columns("full")
    # kumpulkan error per horizon lintas produk
    agg = {h: [] for h in HORIZONS}

    for pid in config.PRODUCTS:
        model = joblib.load(MODEL_DIR / f"xgb_{pid}.joblib")
        df = fe.build_features(fe.load_product_series(df_all, pid))
        train, val, test = fe.temporal_split(df)
        trainval = pd.concat([train, val]).reset_index(drop=True)

        hist0 = list(trainval["qty_sold"].astype(float).values)
        test = test.reset_index(drop=True)
        tvals = test["qty_sold"].values
        n = len(test)

        max_h = max(HORIZONS)
        # rolling origin tiap 5 hari agar cepat & representatif
        for origin in range(0, n - max_h, 5):
            hist = hist0 + list(tvals[:origin])
            exog_rows = []
            for k in range(max_h):
                hw_label = str(test["holiday_window"].iloc[origin + k])
                ex = {
                    "date": test["date"].iloc[origin + k],
                    "is_weekend": int(test["is_weekend"].iloc[origin + k]),
                    "is_holiday": int(test["is_holiday"].iloc[origin + k]),
                    "rainfall_mm": float(test["rainfall_mm"].iloc[origin + k]),
                }
                for label, col in HW_ONEHOT.items():
                    ex[col] = 1 if hw_label == label else 0
                exog_rows.append(ex)
            preds = recursive_forecast(model, hist, exog_rows, feats)
            actual = tvals[origin:origin + max_h]
            for h in HORIZONS:
                agg[h].append((actual[:h], preds[:h]))

    print("=" * 56)
    print("AKURASI NYATA PER HORIZON (recursive backtest, 3 produk)")
    print("=" * 56)
    print(f"{'Horizon':<10}{'MAPE (%)':<12}{'Akurasi (%)':<14}{'RMSE':<10}")
    results = {}
    for h in HORIZONS:
        all_true = np.concatenate([a for a, _ in agg[h]])
        all_pred = np.concatenate([p for _, p in agg[h]])
        mape = ev.mape(all_true, all_pred)
        rmse = ev.rmse(all_true, all_pred)
        akur = round(100 - mape, 1)
        results[h] = {"mape": round(mape, 2), "akurasi": akur, "rmse": round(rmse, 2)}
        print(f"H+{h:<8}{mape:<12.2f}{akur:<14.1f}{rmse:<10.2f}")
    print("=" * 56)
    import json
    with open(MODEL_DIR / "akurasi_horizon.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Tersimpan: models_trained/akurasi_horizon.json")


if __name__ == "__main__":
    main()
