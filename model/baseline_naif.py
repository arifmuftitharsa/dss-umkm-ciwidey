"""
baseline_naif.py - Baseline sederhana sebagai lantai pembanding model ML.

Dihitung pada periode test yang sama dengan pipeline utama (20 Jul-31 Des 2025):
  - naive          : y_t = y_{t-1}
  - seasonal naive : y_t = y_{t-7}
  - moving average : y_t = rata-rata 7 hari terakhir

Output: outputs/hasil_baseline_naif.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path

DATA = Path("data_sintetis_permintaan.csv")
OUT = Path("outputs"); OUT.mkdir(exist_ok=True)
TEST_START = pd.Timestamp("2025-07-20")   # samakan dgn split 70/15/15 di BAB III


def _metrics(y_true, y_pred):
    mask = ~np.isnan(y_pred)
    a, p = y_true[mask], y_pred[mask]
    mae = np.mean(np.abs(a - p))
    rmse = np.sqrt(np.mean((a - p) ** 2))
    mape = np.mean(np.abs((a - p) / a)) * 100
    return mae, rmse, mape


def main():
    df = pd.read_csv(DATA, parse_dates=["date"])
    rows = []
    for pid, g in df.groupby("product_id"):
        g = g.sort_values("date").reset_index(drop=True)
        y = g["qty_sold"].astype(float)
        preds = {
            "Naive (y_t-1)": y.shift(1),
            "Seasonal naive (y_t-7)": y.shift(7),
            "Moving average 7": y.shift(1).rolling(7).mean(),
        }
        test_mask = (g["date"] >= TEST_START).values
        yt = y.values[test_mask]
        for name, pred in preds.items():
            mae, rmse, mape = _metrics(yt, pred.values[test_mask])
            rows.append({"product": pid, "baseline": name,
                         "MAE": round(mae, 2), "RMSE": round(rmse, 2),
                         "MAPE": round(mape, 2)})

    res = pd.DataFrame(rows)
    avg = (res.groupby("baseline")[["MAE", "RMSE", "MAPE"]].mean()
              .round(2).reset_index())
    avg.insert(0, "product", "RATA-RATA")
    res = pd.concat([res, avg], ignore_index=True)
    res.to_csv(OUT / "hasil_baseline_naif.csv", index=False)
    print(res.to_string(index=False))
    print(f"\nDisimpan ke {OUT / 'hasil_baseline_naif.csv'}")


if __name__ == "__main__":
    main()
