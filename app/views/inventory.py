"""
views/inventory.py - Halaman Stok & Pembelian.

Menampilkan status stok, daftar belanja, dan perkiraan kebutuhan bahan baku.
Yang ditampilkan adalah hasil keputusan (beli apa, berapa, kapan); rumus
EOQ/ROP dihitung di core/inventory.py.
"""
import streamlit as st
import pandas as pd

from components import ui, charts
from core.inventory import inventory_table, material_demand_7d
from config import BAHAN_BAKU

NO_BAR = {"displayModeBar": False}


def render(df):
    st.markdown("## Stok & Pembelian")
    st.markdown('<div class="section-sub">Kondisi stok bahan baku dan rekomendasi '
                'belanja minggu ini</div>', unsafe_allow_html=True)

    inv = inventory_table(df)
    perlu = inv[inv["Perlu Order"]]

    c1, c2, c3 = st.columns(3)
    with c1:
        ui.kpi("Bahan Dipantau", f"{len(inv)}", "jenis bahan baku")
    with c2:
        ui.kpi("Perlu Dibeli", f"{len(perlu)}", "minggu ini")
    with c3:
        aman = (inv.Status == "Aman").sum()
        ui.kpi("Stok Aman", f"{aman}", "tidak perlu tindakan")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- daftar belanja
    ui.section("Daftar Belanja Minggu Ini", "Disusun otomatis dari perkiraan penjualan")
    if len(perlu) == 0:
        ui.action("Tidak ada pembelian mendesak",
                  "Semua bahan baku masih di atas batas aman.", "aman")
    else:
        for _, r in perlu.iterrows():
            level = "kritis" if r.Status == "Kritis" else "waspada"
            judul = f"{r['Bahan Baku']} — beli ± {r['Saran Order (≈EOQ)']:.0f} {r['Satuan']}"
            detail = (f"Stok sekarang {r['Stok']} {r['Satuan']}, "
                      f"batas aman {r['ROP']:.0f} {r['Satuan']}. "
                      f"Pesanan biasanya tiba {r['Lead Time (hari)']} hari "
                      f"({r['Pemasok']}).")
            ui.action(judul, detail, level)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- tabel stok (bahasa awam, status pill)
    ui.section("Kondisi Semua Bahan Baku", "")
    tampil = inv.copy()
    tampil["Kondisi"] = tampil["Status"].apply(ui.pill)
    tampil["Stok sekarang"] = tampil["Stok"].astype(str) + " " + tampil["Satuan"]
    tampil["Batas aman"] = tampil["ROP"].round().astype(int).astype(str) + " " + tampil["Satuan"]
    tampil["Jumlah beli ideal (EOQ)"] = tampil["EOQ"].round().astype(int).astype(str) + " " + tampil["Satuan"]
    tampil["Pakai per hari"] = tampil["Kebutuhan/hari (D̄)"].round(1).astype(str) + " " + tampil["Satuan"]
    st.markdown(
        tampil[["Bahan Baku", "Stok sekarang", "Batas aman", "Jumlah beli ideal (EOQ)",
                "Pakai per hari", "Kondisi"]].to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )
    st.caption("Batas aman = ROP (titik pesan ulang) · Jumlah beli ideal = EOQ "
               "(kuantitas optimal sekali pesan).")

    st.markdown("<br>", unsafe_allow_html=True)
    ui.section("Posisi Stok terhadap Batas Aman",
               "Garis biru = batas aman (ROP) · garis kuning = jumlah beli ideal (EOQ)")
    st.plotly_chart(charts.inventory_bar(inv), use_container_width=True, config=NO_BAR)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- kebutuhan bahan baku minggu ini (hasil konversi, dijelaskan awam)
    with st.expander("Lihat perkiraan pemakaian bahan baku 7 hari ke depan"):
        st.caption("Dihitung dari perkiraan penjualan semua produk × resep tiap produk.")
        mat = material_demand_7d(df)
        mat_show = mat.copy()
        mat_show.index = pd.to_datetime(mat_show.index).strftime("%a %d %b")
        mat_show.columns = [BAHAN_BAKU[c]["nama"] for c in mat_show.columns]
        st.dataframe(mat_show, use_container_width=True)
