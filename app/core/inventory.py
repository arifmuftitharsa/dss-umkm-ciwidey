"""
core/inventory.py - Forecast -> kebutuhan bahan baku -> keputusan inventori.

Persamaan Sec. 3.6:
  BOM        : D_m,t = sum_k yhat_k,t * BOM_k,m
  EOQ        : EOQ_m = sqrt(2 * Dbar_m * S_m / H_m)
  ROP        : ROP_m = Dbar_m * L_m + Z * sigma_m * sqrt(L_m)
  Safety stock = Z * sigma_m * sqrt(L_m)  (komponen kedua ROP)
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import (BAHAN_BAKU, BOM, PRODUK, PEMASOK, Z_SCORE)
from core.forecasting import forecast_future


def _sumber_data():
    """Ambil bahan baku & BOM dari database (edit pemilik). Fallback ke config."""
    try:
        from data import store
        store.init_db()
        bahan = store.get_bahan_dict()
        bom = store.get_bom_dict()
        if bahan and bom:
            return bahan, bom
    except Exception:
        pass
    return BAHAN_BAKU, BOM


def material_demand_7d(df) -> pd.DataFrame:
    """
    Hitung kebutuhan tiap bahan baku per hari (7 hari ke depan) dari forecast
    seluruh produk via BOM, lalu agregasi.
    Mengembalikan DataFrame: date x material (kebutuhan harian) + sigma per material.
    """
    # forecast 7 hari untuk semua produk
    per_produk = {}
    sigma_produk = {}
    for pid in PRODUK:
        _, fut, sig = forecast_future(df, pid)
        per_produk[pid] = fut.set_index("date")["yhat"]
        sigma_produk[pid] = sig

    dates = next(iter(per_produk.values())).index
    mat_daily = pd.DataFrame(index=dates)

    bahan_src, bom_src = _sumber_data()
    for mid in bahan_src:
        total = np.zeros(len(dates))
        var = 0.0  # propagasi varians untuk sigma bahan baku
        for pid, bom in bom_src.items():
            coef = bom.get(mid, 0.0)
            if coef and pid in per_produk:
                total += per_produk[pid].to_numpy() * coef
                var += (coef * sigma_produk[pid]) ** 2
        mat_daily[mid] = np.round(total, 2)
        mat_daily.attrs.setdefault("sigma", {})[mid] = np.sqrt(var)

    return mat_daily


def eoq(dbar: float, S: float, H: float) -> float:
    if dbar <= 0 or H <= 0:
        return 0.0
    return float(np.sqrt(2 * dbar * S / H))


def rop(dbar: float, lead: int, sigma: float) -> tuple[float, float]:
    """Kembalikan (ROP, safety_stock)."""
    ss = Z_SCORE * sigma * np.sqrt(lead)
    return float(dbar * lead + ss), float(ss)


def inventory_table(df) -> pd.DataFrame:
    """
    Tabel status inventori per bahan baku: stok, Dbar (7hr), EOQ, ROP, SS,
    status (Kritis/Waspada/Aman), pemasok, lead time, rekomendasi order.
    """
    mat = material_demand_7d(df)
    sigma_map = mat.attrs.get("sigma", {})
    bahan_src, _ = _sumber_data()

    rows = []
    for mid, b in bahan_src.items():
        seri = mat[mid]
        dbar = float(seri.mean())                     # rata-rata kebutuhan harian
        sigma = float(sigma_map.get(mid, seri.std())) # ketidakpastian (dari forecast)
        Q = eoq(dbar, b["S"], b["H"])
        rp, ss = rop(dbar, b["lead_time"], sigma)
        stok = b["stok"]

        # status berdasar posisi stok terhadap ROP
        if stok <= rp:
            status = "Kritis"
        elif stok <= rp * 1.3:
            status = "Waspada"
        else:
            status = "Aman"

        butuh_order = status in ("Kritis", "Waspada")
        rows.append({
            "Kode": mid,
            "Bahan Baku": b["nama"],
            "Satuan": b["satuan"],
            "Stok": stok,
            "Kebutuhan/hari (D̄)": round(dbar, 2),
            "Kebutuhan 7 hari": round(dbar * 7, 1),
            "EOQ": round(Q, 1),
            "ROP": round(rp, 1),
            "Safety Stock": round(ss, 1),
            "Lead Time (hari)": b["lead_time"],
            "Pemasok": PEMASOK.get(b.get("pemasok", "S1"), {}).get("nama", "—"),
            "Status": status,
            "Perlu Order": butuh_order,
            "Saran Order (≈EOQ)": round(Q, 0) if butuh_order else 0,
        })
    return pd.DataFrame(rows)


def simulasi_skenario(df) -> dict:
    """
    Ringkasan evaluasi sistem (Sec. 3.6.5): Skenario A (manual) vs B (sistem).
    Angka ilustratif prototipe yang konsisten dengan klaim literatur
    (Calderon 2025: inventori turun ~50%, MAE turun). Pada Bab IV diisi hasil riil.
    """
    return {
        "A": {"nama": "Manual (tanpa sistem)", "stockout_rate": 18.5, "avg_inventory_days": 11.4},
        "B": {"nama": "Dengan DSS (EOQ/ROP)",  "stockout_rate": 4.2,  "avg_inventory_days": 6.1},
    }
