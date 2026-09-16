"""
app.py - Entry point Streamlit.

Prototipe Decision Support System (DSS) manajemen stok UMKM sektor wisata.
Studi kasus: UMKM Olahan Stroberi, Desa Wisata Alamendah, Ciwidey.

Jalankan:  streamlit run app.py
"""
import streamlit as st

from components import ui
from data.synthetic import generate
from config import APP_NAME, WARNA
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
# st.navigation(position="sidebar") SELALU render widget nav di PALING ATAS
# sidebar -- dikonfirmasi dari dokumentasi resmi (help(st.navigation)):
# "the navigation widget appears at the top of the sidebar". Ini KETERBATASAN
# API, bukan keputusan desain: urutan pemanggilan kode di bawah TIDAK
# mengubah posisi render nav -- nama app+tagline SELALU tampil di bawah nav
# apa pun urutan kodenya. Diterima apa adanya (bukan diakali) -- alternatif
# satu-satunya, position="top", pindah nav jadi header horizontal di atas
# konten (ganti paradigma navigasi total), di luar scope perbaikan kecil ini.
nav = st.navigation(pages, position="sidebar")

# --- SIDEBAR -- nama app + tagline. Sengaja sederhana (nama+tagline+garis,
# SELESAI) -- info Studi kasus/Rentang Waktu dan disclaimer riset dihapus
# dari sini (keputusan Arif); disclaimer data sintetis (prinsip T-15) TETAP
# berlaku, tanggung jawabnya dipindah ke dokumentasi & penjelasan lisan saat
# onboarding, bukan dihapus dari kesadaran proyek.
with st.sidebar:
    st.markdown(
        f"<div style='font-family:Source Serif 4,serif;font-size:1.25rem;"
        f"font-weight:700;color:{WARNA['teks']};line-height:1.2;margin-top:.5rem;'>{APP_NAME}</div>"
        f"<div class='teks-muted-custom' style='color:{WARNA['teks_lemah']};"
        f"font-size:.8rem;margin-bottom:1rem;'>"
        "Bantu UMKM Kelola Stok</div>"
        "<hr style='margin:0 0 1rem;'>",
        unsafe_allow_html=True,
    )

nav.run()

# --- Atribusi tim -- teks WAJIB persis (permintaan Pak Herry, jangan
# diparafrase/ditambah embel-embel). Ditaruh SEKALI di sini (bukan di
# blok sidebar atas) supaya render di BAWAH nav.run() secara DOM order --
# TAK LAGI relevan untuk posisi visual sejak revisi 16 Sept 2026 (posisi
# sekarang position:absolute ke dasar sidebar via class di bawah, bebas
# dari urutan DOM), tapi ditinggal di sini karena tetap tempat paling
# logis (dekat definisi nav, bukan bercampur blok tagline di atas).
# class="teks-atribusi-tim" (BUKAN "teks-muted-custom" yang dipakai
# tagline) -- sengaja dipisah (lihat components/ui.py) supaya ukuran
# atribusi (1rem) independen, tak ikut kalau tagline (.8rem) diubah lagi
# nanti atau sebaliknya. Style inline dihapus (font-size/position semua
# sekarang di CSS class), cuma teks mentahnya yang tersisa di sini.
with st.sidebar:
    st.markdown(
        "<div class='teks-atribusi-tim'>"
        "Aplikasi ini dikembangkan oleh tim UPERAISAL - Universitas Pertamina</div>",
        unsafe_allow_html=True,
    )
