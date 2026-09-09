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
from data import store
from config import WARNA

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
            judul = f"{r['Bahan Baku']}, beli ± {r['Saran Order (≈EOQ)']:.0f} {r['Satuan']}"
            detail = (f"Stok sekarang {ui.format_angka(r['Stok'])} {r['Satuan']}, "
                      f"batas aman {r['ROP']:.0f} {r['Satuan']}. "
                      f"Pesanan biasanya tiba {r['Lead Time (hari)']} hari "
                      f"({r['Pemasok']}).")
            ui.action(judul, detail, level)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- tabel stok (bahasa awam, status pill)
    ui.section("Kondisi Semua Bahan Baku", "Semua bahan baku dan levelnya saat ini")
    tampil = inv.copy()
    tampil["Kondisi"] = tampil["Status"].apply(ui.pill)
    # temuan audit #1: ui.format_angka() (bulat tanpa .0 tak perlu, tetap
    # tampilkan desimal kalau memang pecahan) -- sebelumnya str() mentah,
    # "42.0 kg" dsb, sudah diperbaiki di halaman Ringkasan Operasional tapi
    # terlewat di sini.
    tampil["Stok sekarang"] = tampil["Stok"].apply(ui.format_angka) + " " + tampil["Satuan"]
    tampil["Batas aman"] = tampil["ROP"].round().astype(int).astype(str) + " " + tampil["Satuan"]
    tampil["Jumlah beli ideal (EOQ)"] = tampil["EOQ"].round().astype(int).astype(str) + " " + tampil["Satuan"]
    tampil["Pakai per hari"] = tampil["Kebutuhan/hari (D̄)"].round(1).astype(str) + " " + tampil["Satuan"]
    tabel_html = tampil[["Bahan Baku", "Stok sekarang", "Batas aman",
                        "Jumlah beli ideal (EOQ)", "Pakai per hari",
                        "Kondisi"]].to_html(escape=False, index=False)
    st.markdown(f'<div class="tabel-scroll">{tabel_html}</div>', unsafe_allow_html=True)
    st.caption("Batas aman = ROP (titik pesan ulang), jumlah beli ideal = EOQ "
               "(kuantitas optimal sekali pesan).")

    st.markdown("<br>", unsafe_allow_html=True)
    ui.section("Posisi Stok terhadap Batas Aman",
               "Perbandingan visual stok vs batas aman")
    ui.legend([
        (WARNA["kritis_bar"], "Segera beli"),
        (WARNA["waspada_bar"], "Perhatikan"),
        (WARNA["aman_bar"], "Aman"),
        (WARNA["teks"], "Batas aman (ROP)"),
        ("#F4B400", "Jumlah beli ideal (EOQ)"),
    ])
    st.plotly_chart(charts.inventory_bar(inv), use_container_width=True, config=NO_BAR)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- kebutuhan bahan baku minggu ini (hasil konversi, dijelaskan awam)
    with st.expander("Lihat perkiraan pemakaian bahan baku 7 hari ke depan"):
        st.caption("Dihitung dari perkiraan penjualan semua produk × resep tiap produk.")
        mat = material_demand_7d(df)
        mat_show = mat.copy()
        mat_show.index = [ui.tanggal_id(d, hari_penuh=False)
                          for d in pd.to_datetime(mat_show.index)]
        # temuan audit #2: BAHAN_BAKU statis (config.py) diganti
        # store.get_bahan_dict() (dinamis, database) -- pola identik T-4 asli
        # (produk baru via dashboard tak dikenal config statis, KeyError).
        # Bahan baku baru yang ditambah lewat Manajemen & Pengaturan (kode
        # bebas, tak wajib ada di config.py) sebelumnya bikin expander ini
        # crash saat dibuka -- store.get_bahan_dict() SELALU sinkron dgn apa
        # pun yang ada di database, sama seperti material_demand_7d() sendiri
        # (lewat _sumber_data()) sudah ambil dari sumber yang sama.
        bahan_dinamis = store.get_bahan_dict()
        mat_show.columns = [bahan_dinamis[c]["nama"] for c in mat_show.columns]
        # temuan audit #3: presisi desimal antar-sel tak konsisten (mis. 3
        # tampil "3" tapi 5.28 tampil "5.28" di kolom sama) -- st.dataframe
        # render float mentah, trailing zero otomatis hilang per-sel.
        # column_config format="%.1f" paksa SEMUA sel satu desimal seragam,
        # kolom jadi lebih gampang dibandingkan sekilas.
        st.dataframe(
            mat_show, use_container_width=True,
            column_config={
                kolom: st.column_config.NumberColumn(format="%.1f")
                for kolom in mat_show.columns
            },
        )
