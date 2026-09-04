"""
inventory.py - Modul inventori (Sec. 3.6.3-3.6.5).

- 3.6.3 konversi forecast produk -> kebutuhan bahan baku via BOM
- 3.6.4 EOQ, ROP, dan safety stock
- 3.6.5 simulasi Skenario A (manual) vs B (DSS): stockout & inventory days
"""

import numpy as np
import pandas as pd

import config


# --- 3.6.3 Konversi forecast permintaan -> kebutuhan bahan baku
def forecast_to_materials(product_forecasts):
    """
    product_forecasts : dict {product_id: array forecast harian (unit)}
    Mengembalikan dict {material_id: array kebutuhan harian (satuan bahan)}.
    D_{m,t} = Σ_k yhat_{k,t} · BOM_{k,m}
    """
    horizon = len(next(iter(product_forecasts.values())))
    materials = {}
    for mat, bom_row in config.BOM.items():
        demand = np.zeros(horizon)
        for pid, fc in product_forecasts.items():
            demand += np.asarray(fc, float) * bom_row.get(pid, 0)
        materials[mat] = demand
    return materials


# --- 3.6.4 EOQ, ROP, Safety Stock
def compute_eoq(avg_demand, ordering_cost, holding_cost):
    """EOQ = sqrt(2·D·S / H)  (Eq. 3.4)."""
    if holding_cost <= 0:
        return 0.0
    return float(np.sqrt(2 * avg_demand * ordering_cost / holding_cost))


def compute_rop(avg_demand, lead_time, std_demand, z=config.SERVICE_LEVEL_Z):
    """ROP = d·L + Z·σ·sqrt(L)  (Eq. 3.5). Safety stock = Z·σ·sqrt(L)."""
    safety_stock = z * std_demand * np.sqrt(lead_time)
    rop = avg_demand * lead_time + safety_stock
    return float(rop), float(safety_stock)


def inventory_recommendation(material_demand_series, mat_id):
    """
    Hitung EOQ/ROP/SS untuk satu bahan baku dari deret kebutuhan harian.
    avg & std diambil dari distribusi forecast (bukan data historis statis) —
    sesuai keunggulan pendekatan ML di Section 3.6.4.
    """
    p = config.INVENTORY_PARAMS[mat_id]
    avg_d = float(np.mean(material_demand_series))
    std_d = float(np.std(material_demand_series))
    eoq = compute_eoq(avg_d, p["ordering_cost"], p["holding_cost"])
    rop, ss = compute_rop(avg_d, p["lead_time"], std_d)
    return {
        "material": config.MATERIALS[mat_id],
        "avg_demand": round(avg_d, 2),
        "std_demand": round(std_d, 2),
        "lead_time": p["lead_time"],
        "EOQ": round(eoq, 2),
        "ROP": round(rop, 2),
        "safety_stock": round(ss, 2),
    }


# --- 3.6.5 Simulasi inventori: Skenario A (manual) vs B (DSS)
def simulate_inventory(actual_demand, mode, forecast_demand=None, mat_id=None):
    """
    actual_demand   : array kebutuhan bahan baku AKTUAL harian (proksi = data test)
    mode            : 'A' (manual) atau 'B' (DSS)
    forecast_demand : array forecast (untuk mode B)
    Mengembalikan dict {stockout_rate (%), avg_inventory_days}.

    Skenario A: pesan = rata-rata permintaan 14 hari terakhir, tiap awal minggu.
    Skenario B: pesan = EOQ saat stok ≤ ROP, berbasis forecast.
    """
    n = len(actual_demand)
    p = config.INVENTORY_PARAMS[mat_id]
    lead = p["lead_time"]

    stock = float(np.mean(actual_demand[:14])) * lead  # stok awal wajar
    stockout_days = 0
    inv_days_record = []
    pending = []  # (arrival_day, qty)

    if mode == "B":
        rec = inventory_recommendation(forecast_demand, mat_id)
        eoq, rop = rec["EOQ"], rec["ROP"]

    for t in range(n):
        # Terima barang yang tiba hari ini
        arrived = sum(q for d, q in pending if d == t)
        stock += arrived
        pending = [(d, q) for d, q in pending if d != t]

        if mode == "A":
            # pesan tiap awal minggu (t % 7 == 0) sejumlah rata-rata 14 hari terakhir
            if t % 7 == 0:
                lo = max(0, t - 14)
                order_qty = float(np.mean(actual_demand[lo:t])) * 7 if t > 0 \
                    else float(np.mean(actual_demand[:14])) * 7
                pending.append((t + lead, order_qty))
        else:  # mode B — reorder berbasis ROP/EOQ
            on_order = sum(q for _, q in pending)
            if stock + on_order <= rop:
                pending.append((t + lead, eoq))

        # Penuhi permintaan aktual hari ini
        demand_t = actual_demand[t]
        if stock >= demand_t:
            stock -= demand_t
        else:
            stockout_days += 1
            stock = 0

        # catat inventory days (stok / rata-rata permintaan)
        avg_dem = max(np.mean(actual_demand), 1e-6)
        inv_days_record.append(stock / avg_dem)

    return {
        "stockout_rate": round(stockout_days / n * 100, 2),
        "avg_inventory_days": round(float(np.mean(inv_days_record)), 2),
    }
