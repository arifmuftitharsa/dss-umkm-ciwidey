"""
feature_engineering.py - Prapemrosesan & rekayasa fitur (Sec. 3.3).

- 3.3.3 fitur XGBoost : lag (1/7/14), rolling (mean 7/30, std 7),
                        one-hot day_of_week, one-hot holiday_window
- 3.3.4 normalisasi   : StandardScaler, fit hanya di data train
- 3.3.5 pembagian data: temporal 70/15/15 tanpa shuffling
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

import config

# holiday_window di-one-hot (bukan ordinal): nilai ordinal untuk "bukan libur"
# akan dibaca model pohon sebagai angka besar yang menyesatkan.
# Non-libur = semua kolom 0.
HW_ONEHOT = {"H-1": "hw_hm1", "H": "hw_h0", "H+1": "hw_hp1", "H+2": "hw_hp2"}
HW_COLS = ["hw_hm1", "hw_h0", "hw_hp1", "hw_hp2"]

DOW_NAMES = ["dow_mon", "dow_tue", "dow_wed", "dow_thu", "dow_fri", "dow_sat", "dow_sun"]


def load_product_series(df_all, product_id):
    """Ambil deret satu produk, urut tanggal, set index harian."""
    df = df_all[df_all["product_id"] == product_id].copy()
    df = df.sort_values("date").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])
    return df


def build_features(df):
    """
    Bangun feature matrix untuk XGBoost (Section 3.3.3).
    Seluruh lag/rolling dihitung dari data hari sebelumnya (shift) untuk
    menghindari kebocoran data masa depan.
    """
    df = df.copy()
    y = df["qty_sold"].astype(float)

    # Fitur lag (3.3.3)
    for lag in config.LAG_FEATURES:
        df[f"lag_{lag}"] = y.shift(lag)

    # Fitur rolling — dihitung dari shift(1) agar tidak bocor (3.3.3)
    for w in config.ROLLING_WINDOWS:
        df[f"roll_mean_{w}"] = y.shift(1).rolling(window=w).mean()
    df["roll_std_7"] = y.shift(1).rolling(window=7).std()

    # One-hot day_of_week (3.3.3)
    dow = df["date"].dt.dayofweek  # 0=Senin..6=Minggu
    for i, name in enumerate(DOW_NAMES):
        df[name] = (dow == i).astype(int)

    # One-hot holiday_window: 4 kolom biner, non-libur = semua 0
    hw = df["holiday_window"].astype(str)
    for label, col in HW_ONEHOT.items():
        df[col] = (hw == label).astype(int)

    return df


def get_feature_columns(scenario="full"):
    """
    Daftar kolom fitur per skenario ablation (Sec. 3.6.2).
    Baseline benar-benar hanya lag+rolling; day-of-week ditambahkan bertahap
    agar efek akhir pekan tidak "bocor" lewat fitur kalender pada baseline.

      A (baseline) : lag + rolling saja (pola internal deret murni)
      B (+dow)     : A + one-hot day_of_week
      C (+weekend) : B + is_weekend
      D (+holiday) : C + is_holiday + one-hot holiday_window
      E (full)     : D + rainfall_mm
    """
    base = [f"lag_{l}" for l in config.LAG_FEATURES]
    base += [f"roll_mean_{w}" for w in config.ROLLING_WINDOWS] + ["roll_std_7"]

    if scenario == "A":
        return base
    if scenario == "B":
        return base + DOW_NAMES
    if scenario == "C":
        return base + DOW_NAMES + ["is_weekend"]
    if scenario == "D":
        return base + DOW_NAMES + ["is_weekend", "is_holiday"] + HW_COLS
    # E / full
    return base + DOW_NAMES + ["is_weekend", "is_holiday"] + HW_COLS + ["rainfall_mm"]


def temporal_split(df):
    """Pembagian 70/15/15 tanpa shuffling (Section 3.3.5)."""
    n = len(df)
    n_train = int(n * config.TRAIN_RATIO)
    n_val = int(n * config.VAL_RATIO)
    train = df.iloc[:n_train].copy()
    val = df.iloc[n_train:n_train + n_val].copy()
    test = df.iloc[n_train + n_val:].copy()
    return train, val, test


def scale_features(train, val, test, feature_cols):
    """
    StandardScaler di-fit hanya di train (Section 3.3.4).
    Mengembalikan salinan ter-scale + objek scaler.
    """
    scaler = StandardScaler()
    train = train.copy()
    val = val.copy()
    test = test.copy()

    train[feature_cols] = scaler.fit_transform(train[feature_cols])
    val[feature_cols] = scaler.transform(val[feature_cols])
    test[feature_cols] = scaler.transform(test[feature_cols])
    return train, val, test, scaler


if __name__ == "__main__":
    df_all = pd.read_csv(config.DATA_PATH)
    print(f"Total baris dataset: {len(df_all)}")
    for pid in config.PRODUCTS:
        df = load_product_series(df_all, pid)
        df = build_features(df)
        train, val, test = temporal_split(df)
        print(f"\n{pid} — train={len(train)}, val={len(val)}, test={len(test)}")
        print(f"  Periode train : {train['date'].min().date()} – {train['date'].max().date()}")
        print(f"  Periode val   : {val['date'].min().date()} – {val['date'].max().date()}")
        print(f"  Periode test  : {test['date'].min().date()} – {test['date'].max().date()}")
        fc = get_feature_columns("full")
        print(f"  Jumlah fitur (full): {len(fc)}")
