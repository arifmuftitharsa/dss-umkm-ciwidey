"""
app.py - Entry point Streamlit.

Prototipe Decision Support System (DSS) manajemen stok UMKM sektor wisata.
Studi kasus: UMKM Olahan Stroberi, Desa Wisata Alamendah, Ciwidey.

Jalankan:  streamlit run app.py
"""
import streamlit as st

from components import ui
from data.synthetic import generate
from config import STUDI_KASUS, APP_NAME, WARNA
from views import overview, forecasting, inventory, pengaturan

st.set_page_config(
    page_title=f"Kelola Stok UMKM Bareng {APP_NAME}",
    page_icon="📦", layout="wide", initial_sidebar_state="expanded",
)
ui.inject()


@st.cache_data(show_spinner="Membangkitkan dataset sintetis…")
def load_data():
    """Generate sekali, cache antar rerun (deterministik, seed=42)."""
    return generate()


df = load_data()


# --- HALAMAN -- pembungkus tanpa argumen (syarat st.Page/st.navigation),
# menutup atas `df` lewat closure. Isi views/ SENDIRI tidak disentuh (Tahap 1).
def _halaman_ringkasan():
    overview.render(df)


def _halaman_perkiraan():
    forecasting.render(df)


def _halaman_stok():
    inventory.render(df)


def _halaman_manajemen():
    pengaturan.render()          # halaman ini tidak butuh df


pages = [
    st.Page(_halaman_ringkasan, title="Ringkasan Operasional", icon="📊"),
    st.Page(_halaman_perkiraan, title="Perkiraan Penjualan", icon="📈"),
    st.Page(_halaman_stok, title="Stok & Pembelian", icon="📦"),
    st.Page(_halaman_manajemen, title="Manajemen & Pengaturan", icon="⚙️"),
]
# st.navigation menaruh daftar halaman di ATAS sidebar secara otomatis
# (perilaku bawaan Streamlit, tak bisa diubah posisinya) -- adaptif ke
# hamburger/collapsible di layar sempit tanpa CSS/JS custom.
nav = st.navigation(pages, position="sidebar")

# --- SIDEBAR -- info tambahan, dirender DI BAWAH daftar navigasi bawaan
with st.sidebar:
    st.markdown(
        f"<div style='font-family:Source Serif 4,serif;font-size:1.25rem;"
        f"font-weight:700;color:{WARNA['teks']};line-height:1.2;margin-top:.5rem;'>{APP_NAME}</div>"
        f"<div style='color:{WARNA['teks_lemah']};font-size:.8rem;margin-bottom:1rem;'>"
        "Bantu UMKM Kelola Stok</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        f"<div style='font-size:.78rem;color:{WARNA['teks_lemah']};line-height:1.5;'>"
        f"<b>Studi kasus</b><br>{STUDI_KASUS['lokasi']}<br><br>"
        f"<b>Rentang Waktu</b><br>7 hari ke depan (utama) serta 14/30 hari ke depan</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='position:fixed;bottom:14px;font-size:.7rem;color:{WARNA['teks_lemah']};'>"
        "Prototipe penelitian S1, bukan data produksi</div>",
        unsafe_allow_html=True,
    )

nav.run()
