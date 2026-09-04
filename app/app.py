"""
app.py - Entry point Streamlit.

Prototipe Decision Support System (DSS) manajemen stok UMKM sektor wisata.
Studi kasus: UMKM Olahan Stroberi, Desa Wisata Alamendah, Ciwidey.

Jalankan:  streamlit run app.py
"""
import streamlit as st

from components import ui
from data.synthetic import generate
from config import STUDI_KASUS, MODEL, MODEL_TERBAIK
from views import overview, forecasting, inventory, pengaturan

st.set_page_config(
    page_title="DSS UMKM — Supply Chain & Demand Forecasting",
    page_icon="📦", layout="wide", initial_sidebar_state="expanded",
)
ui.inject()


@st.cache_data(show_spinner="Membangkitkan dataset sintetis…")
def load_data():
    """Generate sekali, cache antar rerun (deterministik, seed=42)."""
    return generate()


df = load_data()

# --- SIDEBAR
with st.sidebar:
    st.markdown(
        "<div style='font-family:Source Serif 4,serif;font-size:1.25rem;"
        "font-weight:700;color:#1B4965;line-height:1.2;'>DSS UMKM</div>"
        "<div style='color:#6B7785;font-size:.8rem;margin-bottom:1rem;'>"
        "Supply Chain & Demand Forecasting</div>",
        unsafe_allow_html=True,
    )

    halaman = st.radio(
        "Navigasi",
        ["Ringkasan Operasional", "Perkiraan Penjualan",
         "Stok & Pembelian", "Manajemen & Pengaturan"],
        label_visibility="collapsed",
    )
    st.caption("Empat halaman operasional untuk pemilik UMKM")

    st.markdown("---")
    st.markdown(
        f"<div style='font-size:.78rem;color:#6B7785;line-height:1.5;'>"
        f"<b>Studi kasus</b><br>{STUDI_KASUS['lokasi']}<br><br>"
        f"<b>Model terbaik</b><br>{MODEL[MODEL_TERBAIK]['label']}<br>"
        f"<b>Horizon</b><br>7 hari ke depan (utama) serta 14/30 hari ke depan</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='position:fixed;bottom:14px;font-size:.7rem;color:#9AA5B1;'>"
        "Prototipe penelitian S1 · bukan data produksi</div>",
        unsafe_allow_html=True,
    )

# --- ROUTER
PAGES = {
    "Ringkasan Operasional": overview,
    "Perkiraan Penjualan": forecasting,
    "Stok & Pembelian": inventory,
}
if halaman == "Manajemen & Pengaturan":
    pengaturan.render()          # halaman ini tidak butuh df
else:
    PAGES[halaman].render(df)
