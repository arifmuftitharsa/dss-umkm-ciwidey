"""
views/forecasting.py - Halaman Perkiraan Penjualan.

Menampilkan perkiraan dari model terpilih untuk horizon 7/14/30 hari beserta
alasan ramai/sepi tiap hari. Pemilihan model dan metrik teknis sengaja tidak
ditampilkan di sini.
"""
import streamlit as st
import pandas as pd

from components import ui, charts
from core.forecasting import forecast_future
from data.weather import MAX_FORECAST_DAYS
from config import PRODUK, MODEL_TERBAIK

NO_BAR = {"displayModeBar": False}


def render(df):
    st.markdown("## Perkiraan Penjualan")
    st.markdown('<div class="section-sub">Perkiraan jumlah terjual per produk '
                'untuk beberapa hari ke depan</div>', unsafe_allow_html=True)

    c_prod, c_hor = st.columns([2, 1])
    with c_prod:
        pid = st.selectbox("Pilih produk", list(PRODUK.keys()),
                           format_func=lambda k: PRODUK[k]["nama"])
    with c_hor:
        horizon = st.selectbox("Horizon perkiraan", [7, 14, 30],
                               format_func=lambda d: f"{d} hari")

    # Hanya horizon 30 yang melewati batas prakiraan cuaca numerik (16 hari).
    if horizon > MAX_FORECAST_DAYS:
        st.warning(
            f"Prakiraan cuaca hanya tersedia sampai hari ke-{MAX_FORECAST_DAYS}. "
            f"Hari ke-{MAX_FORECAST_DAYS + 1} sampai ke-{horizon} memakai rata-rata "
            "curah hujan bulanan Ciwidey, sehingga cocok untuk perencanaan kasar, "
            "bukan keputusan harian."
        )

    hist, fut, _ = forecast_future(df, pid, MODEL_TERBAIK, horizon=horizon)
    satuan = PRODUK[pid]["satuan"]

    total = int(fut.yhat.sum())
    rata = int(fut.yhat.mean())

    # KPI sengaja TANPA angka akurasi/MAPE (T-19) -- data training masih
    # sintetis (T-15), angka apa pun yang menyiratkan "seberapa akurat
    # sistem ini" berisiko menyesatkan pemilik UMKM.
    c1, c2 = st.columns(2)
    with c1:
        ui.kpi(f"Total Perkiraan {horizon} Hari", f"{total} {satuan}", "seluruh periode")
    with c2:
        ui.kpi("Rata-rata per Hari", f"{rata} {satuan}", "untuk persiapan produksi")

    st.markdown("<br>", unsafe_allow_html=True)

    ui.section(f"Grafik Perkiraan — {PRODUK[pid]['nama']}",
               "Garis hijau = perkiraan; area terang = rentang kemungkinan")
    st.plotly_chart(charts.forecast_chart(hist, fut, satuan),
                    use_container_width=True, config=NO_BAR)

    st.markdown("<br>", unsafe_allow_html=True)

    ui.section("Rincian per Hari", "Beserta alasan ramai/sepi")
    tbl = fut.copy()

    def alasan(r):
        if r.is_holiday == 1:
            return "Hari libur — ramai"
        if r.holiday_window in (-1, 1, 2):
            return "Sekitar hari libur"
        if r.is_weekend == 1:
            return "Akhir pekan — ramai"
        if r.rainfall_mm > 20:
            return "Hujan — cenderung sepi"
        return "Hari biasa"

    show = pd.DataFrame({
        "Tanggal": tbl.date.dt.strftime("%A, %d %b"),
        "Perkiraan terjual": tbl.yhat.astype(int).astype(str) + " " + satuan,
        "Catatan": tbl.apply(alasan, axis=1),
    })
    st.dataframe(show, use_container_width=True, hide_index=True)

    ramai = tbl[(tbl.is_holiday == 1) | (tbl.is_weekend == 1)]
    if len(ramai) > 0:
        ui.action(
            "Persiapan untuk hari penjualan tinggi",
            f"Ada {len(ramai)} hari yang diperkirakan lebih tinggi penjualannya minggu ini. "
            "Tambah stok bahan baku dan jadwalkan produksi lebih awal.",
            "info")
