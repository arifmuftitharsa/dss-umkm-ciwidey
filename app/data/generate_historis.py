"""
data/generate_historis.py - Riwayat sintetis untuk produk yang baru ditambah.

Produk baru belum punya riwayat penjualan, padahal model butuh lag/rolling.
Modul ini membangkitkan 1.096 hari riwayat (2023-01-01 s/d 2025-12-31) dengan
formula yang sama seperti Sec. 3.2.2:

    y_t = mu * (1 + S_weekly(t) + H(t) + W(t)) + eps_t

Parameter dikalibrasi dari mu yang diisi pemilik, lalu hasilnya ditambahkan ke
data/historis_penjualan.csv.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

_DATA_DIR = Path(__file__).resolve().parent
_CSV_PATH = _DATA_DIR / "historis_penjualan.csv"

# --- Konstanta kalibasi (sama dengan generate_data_sintetis.py BAB III)
_RAIN_CSV = _DATA_DIR / "cuaca_bandung_aktual.csv"
_DATES = pd.date_range("2023-01-01", "2025-12-31", freq="D")


def _get_holidays():
    try:
        import holidays
        hols = holidays.Indonesia(years=[2023, 2024, 2025])
        return set(hols.keys())
    except Exception:
        return set()


def _get_window(d, holiday_dates):
    d0 = d.date()
    if d0 in holiday_dates:
        return "H"
    for offset, label in [(-1, "H-1"), (1, "H+1"), (2, "H+2")]:
        if (d + pd.Timedelta(days=offset)).date() in holiday_dates:
            return label
    return "---"


def _s_weekly(d):
    dow = d.dayofweek
    if dow == 5:   return 0.80
    elif dow == 6: return 0.50
    elif dow == 4: return 0.10
    return 0.0


def _h_effect(d, holiday_dates):
    d0 = d.date()
    if d0 in holiday_dates:
        return 2.5
    for offset, val in [(-1, 1.2), (1, 1.0), (2, 0.5)]:
        if (d + pd.Timedelta(days=offset)).date() in holiday_dates:
            return val
    return 0.0


def _w_effect(rainfall_mm):
    if rainfall_mm > 20:  return -0.35
    elif rainfall_mm > 10: return -0.15
    return 0.0


def _load_rainfall():
    """Pakai cuaca aktual bila tersedia, fallback ke musiman."""
    if _RAIN_CSV.exists():
        cuaca = pd.read_csv(_RAIN_CSV, parse_dates=["date"]).set_index("date")
        return {d: float(cuaca.loc[d, "rainfall_mm"])
                if d in cuaca.index else 5.0 for d in _DATES}
    # fallback: pola musiman Bandung
    rng = np.random.default_rng(42)
    rain_map = {}
    for d in _DATES:
        wet = d.month in (11, 12, 1, 2, 3)
        base = 9.0 if wet else 2.5
        rain_map[d] = round(float(rng.gamma(0.7, base)), 1)
    return rain_map


def generate_historis_produk(product_id: str, product_name: str,
                              mu: float, seed: int = 42) -> pd.DataFrame:
    """
    Bangkitkan 1096 baris historis sintetis untuk satu produk baru.
    Mengembalikan DataFrame dengan kolom identik historis_penjualan.csv.
    """
    rng = np.random.default_rng(seed)
    holiday_dates = _get_holidays()
    rain_map = _load_rainfall()
    records = []

    for d in _DATES:
        rain = rain_map.get(d, 5.0)
        sw = _s_weekly(d)
        he = _h_effect(d, holiday_dates)
        we = _w_effect(rain)
        signal = mu * (1 + sw + he + we)
        noise = rng.normal(0, 0.10 * mu)
        qty = max(0, round(signal + noise))
        records.append({
            "date": d.strftime("%Y-%m-%d"),
            "product_id": product_id,
            "product_name": product_name,
            "qty_sold": int(qty),
            "is_weekend": 1 if d.dayofweek >= 5 else 0,
            "is_holiday": 1 if d.date() in holiday_dates else 0,
            "holiday_window": _get_window(d, holiday_dates),
            "rainfall_mm": round(rain, 1),
        })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df


def append_to_historis(product_id: str, product_name: str,
                        mu: float, seed: int = 42) -> tuple[bool, str]:
    """
    Generate historis untuk produk baru dan append ke historis_penjualan.csv.
    Mengembalikan (berhasil: bool, pesan: str).
    """
    # cek apakah sudah ada
    if _CSV_PATH.exists():
        existing = pd.read_csv(_CSV_PATH, usecols=["product_id"])
        if product_id in existing["product_id"].values:
            return False, f"Historis untuk {product_id} sudah ada ({len(existing[existing.product_id==product_id])} baris)."

    df_new = generate_historis_produk(product_id, product_name, mu, seed)

    if _CSV_PATH.exists():
        df_new.to_csv(_CSV_PATH, mode="a", header=False, index=False)
    else:
        df_new.to_csv(_CSV_PATH, index=False)

    # reset cache history di forecasting
    try:
        import core.forecasting as fc
        fc._HIST = None
    except Exception:
        pass

    return True, f"✓ {len(df_new)} baris historis sintetis untuk {product_name} berhasil dibuat."


if __name__ == "__main__":
    ok, msg = append_to_historis("P004", "Dodol Stroberi", mu=25)
    print(msg)
    import pandas as pd
    df = pd.read_csv(_CSV_PATH)
    print(f"Total baris sekarang: {len(df)}")
    print(df[df.product_id == "P004"].head(5).to_string(index=False))
