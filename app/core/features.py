"""
core/features.py - Pembangun fitur saat inference.

Menyalin persis rekayasa fitur pada pelatihan (Sec. 3.3.3) agar input model
saat prediksi sama dengan saat dilatih: lag (1/7/14), rolling (mean 7/30,
std 7), one-hot day_of_week, one-hot holiday_window, dan curah hujan.

Urutan FEATURE_COLS harus sama dengan feature_cols di models_trained/meta.json.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

DOW_NAMES = ["dow_mon", "dow_tue", "dow_wed", "dow_thu", "dow_fri", "dow_sat", "dow_sun"]
LAG_FEATURES = [1, 7, 14]
ROLLING_WINDOWS = [7, 30]

# One-hot holiday_window; non-libur -> semua kolom 0 (sama seperti saat training).
HW_ONEHOT = {"H-1": "hw_hm1", "H": "hw_h0", "H+1": "hw_hp1", "H+2": "hw_hp2"}
HW_COLS = ["hw_hm1", "hw_h0", "hw_hp1", "hw_hp2"]


# Peta label window -> ordinal, hanya untuk tampilan di dashboard.
# Model tetap memakai one-hot.
_DISPLAY_ORD = {"H-1": -1, "H": 0, "H+1": 1, "H+2": 2, "---": 9}


def window_to_ord(label: str) -> int:
    """Ordinal ringkas untuk keperluan tampilan (bukan fitur model)."""
    label = str(label)
    if label in _DISPLAY_ORD:
        return _DISPLAY_ORD[label]
    if label.startswith("H-"):
        return -1
    if label.startswith("H+"):
        return 2
    return 9


def window_onehot(label: str) -> dict:
    """Petakan label window ke 4 kolom one-hot. Window panjang Lebaran
    (H-3..H+7) dipetakan ke kolom terdekat yang dikenal model:
      H-2/H-3 -> hw_hm1 (pra-libur); H+3..H+7 -> hw_hp2 (pasca-libur)."""
    d = {c: 0 for c in HW_COLS}
    label = str(label)
    if label in HW_ONEHOT:
        d[HW_ONEHOT[label]] = 1
    elif label.startswith("H-"):
        d["hw_hm1"] = 1
    elif label.startswith("H+"):
        d["hw_hp2"] = 1
    return d


# Urutan kolom harus sama dengan feature_cols di models_trained/meta.json.
FEATURE_COLS = (
    [f"lag_{l}" for l in LAG_FEATURES]
    + [f"roll_mean_{w}" for w in ROLLING_WINDOWS]
    + ["roll_std_7"]
    + DOW_NAMES
    + ["is_weekend", "is_holiday"]
    + HW_COLS
    + ["rainfall_mm"]
)


def build_feature_row(series_hist, date, is_weekend, is_holiday,
                      holiday_window, rainfall_mm):
    """
    Bangun 1 baris fitur untuk satu tanggal ke depan.
    series_hist    : list/array qty historis + prediksi sebelumnya (urut waktu).
    holiday_window : label window ('H-1','H','H+1','H+2','---', dst).
    """
    s = np.asarray(series_hist, dtype=float)
    row = {}

    for lag in LAG_FEATURES:
        row[f"lag_{lag}"] = s[-lag] if len(s) >= lag else s[0]

    for w in ROLLING_WINDOWS:
        window = s[-w:] if len(s) >= w else s
        row[f"roll_mean_{w}"] = float(np.mean(window))
    win7 = s[-7:] if len(s) >= 7 else s
    row["roll_std_7"] = float(np.std(win7, ddof=1)) if len(win7) > 1 else 0.0

    dow = pd.Timestamp(date).dayofweek
    for i, name in enumerate(DOW_NAMES):
        row[name] = 1 if dow == i else 0

    row["is_weekend"] = int(is_weekend)
    row["is_holiday"] = int(is_holiday)
    row.update(window_onehot(holiday_window))
    row["rainfall_mm"] = float(rainfall_mm)

    return [row[c] for c in FEATURE_COLS]
