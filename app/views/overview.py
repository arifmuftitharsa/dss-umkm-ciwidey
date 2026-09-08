"""
views/overview.py - Halaman Ringkasan Operasional.

Ditujukan untuk pemilik UMKM: bahasa sehari-hari, tanpa rumus dan istilah
teknis (MAPE, EOQ, sigma).
"""
import streamlit as st

from components import ui, charts
from core.forecasting import forecast_future
from core.inventory import inventory_table
from data import store
from config import STUDI_KASUS, WARNA

NO_BAR = {"displayModeBar": False}


def render(df):
    st.markdown("## Ringkasan Operasional")
    st.markdown(
        f'<div class="section-sub">{STUDI_KASUS["nama"]}, pantauan minggu ini '
        f'({STUDI_KASUS["horizon_hari"]} hari ke depan)</div>',
        unsafe_allow_html=True,
    )

    # T-4: daftar produk dari database, bukan config.PRODUK statis --
    # produk baru lewat dashboard harus ikut terhitung di halaman ini.
    # Diambil sekali, dipakai ulang di seluruh fungsi (hindari query
    # berulang) -- diteruskan sebagai argumen ke _ada_spike/_ada_libur_nasional.
    produk = store.get_produk_dict()

    inv = inventory_table(df)
    kritis = inv[inv.Status == "Kritis"]
    waspada = inv[inv.Status == "Waspada"]

    total_unit = 0
    for pid in produk:
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
        ada_libur = _ada_libur_nasional(df, produk)
        ui.kpi("Hari Libur Nasional", "Ada" if ada_libur else "Tidak",
               "dalam periode perkiraan" if ada_libur else "tidak ada minggu ini")

    st.markdown("<br>", unsafe_allow_html=True)

    # "Yang Perlu Dilakukan" DI ATAS grafik (susunan vertikal, bukan
    # berdampingan kiri-kanan lagi) -- keputusan Arif: aksi yang perlu
    # dilakukan lebih penting dilihat duluan daripada grafik. Isi kartu
    # (kalimat) TAK diubah, cuma posisinya dipindah.
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
    if _ada_spike(df, produk):
        ui.action(
            "Perkiraan lonjakan penjualan minggu ini",
            "Ada akhir pekan atau hari libur. Penjualan cenderung naik, "
            "siapkan stok lebih banyak.",
            "info")

    st.markdown("<br>", unsafe_allow_html=True)

    # "Produk dengan penjualan tertinggi" (lihat deskripsi section di
    # bawah) -- dulu hardcode "P003" (T-4: kebetulan itu memang mu
    # tertinggi di config lama, 80 vs 40/15, tapi statis). Sekarang
    # dihitung dinamis dari mu di database supaya tetap benar berapa
    # pun produk ditambah/dihapus lewat dashboard.
    pid_utama = max(produk, key=lambda pid: produk[pid]["mu"])
    ui.section(f"Perkiraan Penjualan Produk {produk[pid_utama]['nama']}",
               "Produk dengan penjualan tertinggi.")
    ui.legend([
        (WARNA["sekunder"], "Penjualan sebelumnya"),
        (WARNA["primer"], "Perkiraan 7 hari"),
        (ui.tint(WARNA["primer"], .35), "Rentang kemungkinan"),
        ("#F4B400", "Hari libur / event"),
    ])
    hist, fut, _ = forecast_future(df, pid_utama)
    st.plotly_chart(charts.forecast_chart(hist, fut, produk[pid_utama]["satuan"]),
                    use_container_width=True, config=NO_BAR)
    ui.label_sumbu_tanggal()
    ui.petunjuk_geser("Bisa digeser untuk lihat rentang tanggal lain")

    st.markdown("<br>", unsafe_allow_html=True)

    ui.section("Kondisi Stok Bahan Baku", "")
    ui.legend([
        (WARNA["kritis_bar"], "Segera beli"),
        (WARNA["waspada_bar"], "Perhatikan"),
        (WARNA["aman_bar"], "Aman"),
        (WARNA["teks"], "Batas aman (ROP)"),
        ("#F4B400", "Jumlah beli ideal (EOQ)"),
    ])
    st.plotly_chart(charts.inventory_bar(inv), use_container_width=True, config=NO_BAR)


def _ada_spike(df, produk: dict) -> bool:
    for pid in produk:
        _, fut, _ = forecast_future(df, pid)
        if (fut.is_holiday.sum() > 0) or (fut.is_weekend.sum() > 0):
            return True
    return False


def _ada_libur_nasional(df, produk: dict) -> bool:
    """True bila ada hari libur nasional pada periode perkiraan.

    produk diterima sebagai argumen (bukan query ulang ke database) --
    cukup cek SATU produk, kalender sama untuk semua produk.
    """
    for pid in produk:
        _, fut, _ = forecast_future(df, pid)
        return fut.is_holiday.sum() > 0
    return False
