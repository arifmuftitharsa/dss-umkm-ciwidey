"""
views/overview.py - Halaman Ringkasan Operasional.

Ditujukan untuk pemilik UMKM: bahasa sehari-hari, tanpa rumus dan istilah
teknis (MAPE, EOQ, sigma).
"""
import streamlit as st

from components import ui, charts
from core.forecasting import forecast_future
from core.inventory import inventory_table
from config import PRODUK, STUDI_KASUS

NO_BAR = {"displayModeBar": False}


def render(df):
    st.markdown("## Ringkasan Operasional")
    st.markdown(
        f'<div class="section-sub">{STUDI_KASUS["nama"]} · pantauan minggu ini '
        f'({STUDI_KASUS["horizon_hari"]} hari ke depan)</div>',
        unsafe_allow_html=True,
    )

    inv = inventory_table(df)
    kritis = inv[inv.Status == "Kritis"]
    waspada = inv[inv.Status == "Waspada"]

    total_unit = 0
    for pid in PRODUK:
        _, fut, _ = forecast_future(df, pid)
        total_unit += int(fut.yhat.sum())

    # --- KPI: bahasa pemilik. Sengaja TANPA angka akurasi/MAPE (T-19) --
    # data training masih sintetis (T-15), angka apa pun yang menyiratkan
    # "seberapa akurat sistem ini" berisiko menyesatkan pemilik UMKM.
    c1, c2, c3 = st.columns(3)
    with c1:
        ui.kpi("Perkiraan Penjualan", f"{total_unit:,}".replace(",", "."),
               "total unit 7 hari ke depan")
    with c2:
        ui.kpi("Bahan Perlu Dibeli", f"{len(kritis)}",
               f"{len(waspada)} lainnya mulai menipis")
    with c3:
        ada_libur = _ada_libur_nasional(df)
        ui.kpi("Hari Libur Nasional", "Ada" if ada_libur else "Tidak",
               "dalam periode perkiraan" if ada_libur else "tidak ada minggu ini")

    st.markdown("<br>", unsafe_allow_html=True)

    kiri, kanan = st.columns([1.55, 1])
    with kiri:
        pid_utama = "P003"
        ui.section(f"Perkiraan Penjualan — {PRODUK[pid_utama]['nama']}",
                   "Produk dengan penjualan tertinggi. Garis biru = penjualan 60 hari "
                   "lalu, garis hijau = perkiraan 7 hari, area hijau muda = rentang "
                   "kemungkinan (bisa lebih tinggi/rendah).")
        hist, fut, _ = forecast_future(df, pid_utama)
        st.plotly_chart(charts.forecast_chart(hist, fut, PRODUK[pid_utama]["satuan"]),
                        use_container_width=True, config=NO_BAR)

    with kanan:
        ui.section("Yang Perlu Dilakukan", "Tindakan minggu ini")
        if len(kritis) == 0 and len(waspada) == 0:
            ui.action("Semua stok aman", "Tidak ada pembelian mendesak minggu ini.", "aman")
        for _, r in kritis.iterrows():
            ui.action(
                f"Segera beli {r['Bahan Baku']}",
                f"Stok tinggal {r['Stok']} {r['Satuan']}, sudah di bawah batas aman. "
                f"Disarankan beli sekitar {r['Saran Order (≈EOQ)']:.0f} {r['Satuan']}. "
                f"Pesanan biasanya tiba {r['Lead Time (hari)']} hari.",
                "kritis")
        for _, r in waspada.iterrows():
            ui.action(
                f"{r['Bahan Baku']} mulai menipis",
                f"Stok {r['Stok']} {r['Satuan']}. Siapkan pembelian dalam beberapa hari.",
                "waspada")
        if _ada_spike(df):
            ui.action(
                "Perkiraan lonjakan penjualan minggu ini",
                "Ada akhir pekan atau hari libur. Penjualan cenderung naik — "
                "siapkan stok lebih banyak.",
                "info")

    st.markdown("<br>", unsafe_allow_html=True)

    ui.section("Kondisi Stok Bahan Baku", "Batang merah = perlu dibeli")
    st.plotly_chart(charts.inventory_bar(inv), use_container_width=True, config=NO_BAR)


def _ada_spike(df) -> bool:
    for pid in PRODUK:
        _, fut, _ = forecast_future(df, pid)
        if (fut.is_holiday.sum() > 0) or (fut.is_weekend.sum() > 0):
            return True
    return False


def _ada_libur_nasional(df) -> bool:
    """True bila ada hari libur nasional pada periode perkiraan."""
    for pid in PRODUK:
        _, fut, _ = forecast_future(df, pid)
        if fut.is_holiday.sum() > 0:
            return True
        break  # cukup cek satu produk (kalender sama untuk semua)
    return False
