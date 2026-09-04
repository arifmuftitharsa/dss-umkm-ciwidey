"""
data/synthetic.py - Generator dataset permintaan harian sintetis.

Mengikuti model aditif-multiplikatif Sec. 3.2.2:

    y_t = mu * (1 + S_weekly(t) + H(t) + W(t)) + eps_t

  S_weekly : faktor akhir pekan (Sabtu/Minggu)
  H        : lonjakan hari libur + window H-1..H+2
  W        : penalti cuaca bila curah hujan > 20 mm/hari
  eps      : Gaussian noise, sigma = 10% mu

Kolom eksogen yang dihasilkan: rainfall_mm, is_weekend, is_holiday,
holiday_window (Sec. 3.2.4). Curah hujan di sini disimulasikan mengikuti pola
musiman Bandung; pada forecast nyata dipakai data Open-Meteo (data/weather.py).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import PRODUK, SIM, STUDI_KASUS


# --- Kalender hari libur nasional (disederhanakan untuk prototipe)
# Pada sistem nyata: python-holidays (lihat Tabel Ringkasan Deployment).
_LIBUR = {
    "2023-01-01", "2023-01-22", "2023-02-18", "2023-03-22", "2023-04-07",
    "2023-04-22", "2023-04-23", "2023-05-01", "2023-05-18", "2023-06-01",
    "2023-06-29", "2023-08-17", "2023-09-28", "2023-12-25",
    "2024-01-01", "2024-02-08", "2024-02-10", "2024-03-11", "2024-03-29",
    "2024-03-31", "2024-04-10", "2024-04-11", "2024-05-01", "2024-05-09",
    "2024-05-23", "2024-06-01", "2024-06-17", "2024-07-07", "2024-08-17",
    "2024-09-16", "2024-12-25",
    "2025-01-01", "2025-01-27", "2025-01-29", "2025-03-29", "2025-03-31",
    "2025-04-01", "2025-04-18", "2025-05-01", "2025-05-12", "2025-05-29",
    "2025-06-01", "2025-06-06", "2025-06-27", "2025-08-17", "2025-09-05",
    "2025-12-25",
}


def _holiday_flags(dates: pd.DatetimeIndex):
    """Hasilkan is_holiday dan holiday_window (H-1..H+2) untuk tiap tanggal."""
    libur = pd.to_datetime(sorted(_LIBUR))
    is_hol = dates.isin(libur).astype(int)

    window = np.full(len(dates), 9, dtype=int)  # 9 = bukan periode libur
    lo, hi = SIM["holiday_window"]
    for h in libur:
        for offset in range(lo, hi + 1):
            mask = dates == (h + pd.Timedelta(days=offset))
            window[mask] = offset
    return is_hol, window


def _simulate_rainfall(dates: pd.DatetimeIndex, rng) -> np.ndarray:
    """Curah hujan harian (mm) berpola musiman wilayah Bandung."""
    month = dates.month.values
    # musim hujan (Nov-Mar): basis lebih tinggi
    wet = np.isin(month, [11, 12, 1, 2, 3])
    base = np.where(wet, 9.0, 2.5)
    # distribusi gamma -> banyak hari kering, sebagian hari hujan deras
    rain = rng.gamma(shape=0.7, scale=base)
    rain = np.where(rng.random(len(dates)) < (0.55 if True else 0), rain, rain * 0.2)
    return np.round(rain, 1)


def generate(seed: int | None = None) -> pd.DataFrame:
    """
    Kembalikan DataFrame panjang (long) berisi seluruh produk x tanggal.
    Kolom: date, product_id, product, quantity_sold, price, rainfall_mm,
           is_weekend, is_holiday, holiday_window.
    """
    seed = SIM["seed"] if seed is None else seed
    rng = np.random.default_rng(seed)

    dates = pd.date_range(SIM["tanggal_awal"], SIM["tanggal_akhir"], freq="D")
    is_weekend = (dates.dayofweek >= 5).astype(int)
    is_holiday, holiday_window = _holiday_flags(dates)
    rainfall = _simulate_rainfall(dates, rng)

    # --- komponen W (weather penalty)
    pen_lo, pen_hi = SIM["rain_penalty"]
    W = np.where(
        rainfall > SIM["rain_threshold_mm"],
        rng.uniform(pen_lo, pen_hi, len(dates)),  # -0.40..-0.20
        0.0,
    )

    # --- komponen H (holiday spike + window)
    hmin, hmax = SIM["holiday_mult"]
    H = np.zeros(len(dates))
    # hari-H penuh
    H[is_holiday == 1] = rng.uniform(hmin, hmax, (is_holiday == 1).sum()) - 1.0
    # window effect meluruh (H-1, H+1, H+2 dapat fraksi dari spike)
    decay = {-1: 0.5, 1: 0.6, 2: 0.3}
    for off, frac in decay.items():
        m = (holiday_window == off) & (is_holiday == 0)
        H[m] = (rng.uniform(hmin, hmax, m.sum()) - 1.0) * frac

    # --- komponen S_weekly
    wmin, wmax = SIM["weekend_mult"]
    S = np.where(is_weekend == 1, rng.uniform(wmin, wmax, len(dates)) - 1.0, 0.0)

    rows = []
    for pid, p in PRODUK.items():
        mu = p["mu"]
        eps = rng.normal(0, p["noise_pct"] * mu, len(dates))
        y = mu * (1 + S + H + W) + eps
        y = np.clip(np.round(y), 0, None).astype(int)
        rows.append(pd.DataFrame({
            "date": dates,
            "product_id": pid,
            "product": p["nama"],
            "quantity_sold": y,
            "price": p["harga"],
            "rainfall_mm": rainfall,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "holiday_window": holiday_window,
        }))

    df = pd.concat(rows, ignore_index=True)
    return df


def holiday_label(window_val: int) -> str:
    """Ubah nilai ordinal holiday_window jadi label H-1/H/H+1/H+2/—."""
    return {-1: "H-1", 0: "H", 1: "H+1", 2: "H+2"}.get(window_val, "—")
