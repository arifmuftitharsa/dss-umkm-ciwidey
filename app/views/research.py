"""
views/research.py - Halaman Validasi & Metodologi (opsional, untuk penguji).

Lapisan akademik yang dipisah dari halaman operasional: studi komparatif
model, metrik MAE/RMSE/MAPE, ablation study, formula EOQ/ROP, dan pratinjau
dataset. Halaman ini tidak terdaftar pada navigasi app.py secara default.
"""
import streamlit as st
import pandas as pd

from components import ui, charts
from core.forecasting import evaluate_models, ablation_study
from core.inventory import inventory_table
from data.synthetic import holiday_label
from config import (PRODUK, SIM, MODEL, MODEL_TERBAIK, BAHAN_BAKU, Z_SCORE)

NO_BAR = {"displayModeBar": False}


def render(df):
    st.markdown("## Validasi & Metodologi")
    st.markdown('<div class="section-sub">Lapisan penelitian — untuk keperluan '
                'pengujian skripsi, bukan untuk pemilik UMKM</div>',
                unsafe_allow_html=True)
    ui.action(
        "Catatan untuk penguji",
        "Halaman operasional (Ringkasan, Perkiraan, Stok) ditujukan bagi pemilik "
        "UMKM tanpa keahlian teknis, sehingga rumus & metrik disembunyikan di sana. "
        "Seluruh justifikasi metodologis dikumpulkan di halaman ini.",
        "info")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Perbandingan Model", "Ablation Eksogen", "Dataset Sintetis", "Formula Inventori"])

    # --- TAB 1: studi komparatif
    with tab1:
        pid = st.selectbox("Produk", list(PRODUK), key="rmodel",
                           format_func=lambda k: f"{k} · {PRODUK[k]['nama']}")
        horizon = st.radio("Horizon", ["H+1", "H+7"], horizontal=True, index=1)
        metrics = evaluate_models(df, pid)
        kiri, kanan = st.columns([1, 1])
        with kiri:
            show = metrics[metrics.Horizon == horizon][
                ["Model", "MAE", "RMSE", "MAPE (%)"]].reset_index(drop=True)
            st.dataframe(show, use_container_width=True, hide_index=True)
            best = show.loc[show["MAPE (%)"].idxmin(), "Model"]
            ui.action(f"Model terbaik ({horizon}): {best}",
                      f"MAPE terendah {show['MAPE (%)'].min():.2f}% pada test set "
                      "(Jun–Des 2025).", "aman")
        with kanan:
            st.plotly_chart(charts.model_compare_bar(metrics, horizon),
                            use_container_width=True, config=NO_BAR)
        ui.riset_tag("RQ2 & RQ3 · Sec. 3.5 arsitektur model · Sec. 3.6.1 metrik")
        st.caption("Output model pada prototipe ini placeholder terkalibrasi "
                   "(Hybrid < XGBoost < Prophet < ARIMA). Hasil training riil → Bab IV.")

    # --- TAB 2: ablation
    with tab2:
        pid2 = st.selectbox("Produk", list(PRODUK), key="rabl",
                            format_func=lambda k: f"{k} · {PRODUK[k]['nama']}")
        abl = ablation_study(pid2)
        a, b = st.columns([1, 1])
        with a:
            st.dataframe(abl, use_container_width=True, hide_index=True)
        with b:
            st.plotly_chart(charts.ablation_chart(abl),
                            use_container_width=True, config=NO_BAR)
        ui.action("Temuan",
                  "Penambahan variabel eksogen (weekend → libur → cuaca) menurunkan "
                  "MAPE secara bertahap, mengkonfirmasi kontribusinya.", "info")
        ui.riset_tag("RQ4 · Sec. 3.6.2 ablation study (skenario A–D)")

    # --- TAB 3: dataset
    with tab3:
        n_per = len(df) // len(PRODUK)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Observasi/produk", f"{n_per:,}".replace(",", "."))
        c2.metric("Produk", len(PRODUK))
        c3.metric("Variabel eksogen", 3)
        c4.metric("Model dibandingkan", len(MODEL))

        pid3 = st.selectbox("Produk", list(PRODUK), index=2, key="rdata",
                            format_func=lambda k: f"{k} · {PRODUK[k]['nama']}")
        sub = df[df.product_id == pid3].copy()
        sub["holiday_window"] = sub["holiday_window"].apply(holiday_label)
        prev = sub.tail(14)[["date", "product_id", "quantity_sold", "price",
                             "rainfall_mm", "is_weekend", "is_holiday",
                             "holiday_window"]].copy()
        prev["date"] = prev["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(prev, use_container_width=True, hide_index=True)

        a, b = st.columns([1, 1])
        with a:
            st.plotly_chart(charts.weekly_pattern(df, pid3),
                            use_container_width=True, config=NO_BAR)
        with b:
            st.markdown(f"""
**Parameter generasi — y_t = μ·(1 + S + H + W) + ε**

| Komponen | Nilai |
|---|---|
| μ ({PRODUK[pid3]['nama']}) | {PRODUK[pid3]['mu']} {PRODUK[pid3]['satuan']}/hari |
| Weekend (S) | {SIM['weekend_mult'][0]}–{SIM['weekend_mult'][1]}× |
| Holiday (H) | {SIM['holiday_mult'][0]}–{SIM['holiday_mult'][1]}× |
| Window | H{SIM['holiday_window'][0]} … H+{SIM['holiday_window'][1]} |
| Cuaca (W) | {int(SIM['rain_penalty'][0]*100)}%…{int(SIM['rain_penalty'][1]*100)}% bila hujan >{SIM['rain_threshold_mm']:.0f}mm |
| Noise ε | σ = {int(PRODUK[pid3]['noise_pct']*100)}% μ |
""")
        ui.riset_tag("RQ1 · Sec. 3.2.2 model permintaan · Sec. 3.2.4 rancangan variabel")

    # --- TAB 4: formula inventori
    with tab4:
        st.markdown(f"""
Modul inventori mengubah perkiraan permintaan menjadi keputusan pembelian
melalui tiga formula klasik (Sec. 3.6.4), dengan service level 95% (Z = {Z_SCORE}):

- **EOQ** = √(2 · D̄ · S / H) — jumlah optimal sekali pesan
- **ROP** = D̄ · L + Z · σ · √L — titik harus memesan kembali
- **Safety Stock** = Z · σ · √L — penyangga (komponen kedua ROP)

di mana D̄ = rata-rata kebutuhan harian (dari forecast), S = biaya pesan,
H = biaya simpan, L = lead time pemasok, σ = ketidakpastian forecast.
""")
        inv = inventory_table(df)
        mid = st.selectbox("Bahan baku", list(BAHAN_BAKU),
                           format_func=lambda k: BAHAN_BAKU[k]["nama"])
        r = inv[inv.Kode == mid].iloc[0]
        b = BAHAN_BAKU[mid]
        st.markdown(f"""
| Parameter | Nilai |
|---|---|
| D̄ (kebutuhan harian) | {r['Kebutuhan/hari (D̄)']} {b['satuan']} |
| S (biaya pesan) | Rp {b['S']:,} |
| H (biaya simpan/hari) | Rp {b['H']:,} |
| L (lead time) | {b['lead_time']} hari |
| **EOQ** | **{r['EOQ']:.0f} {b['satuan']}** |
| **ROP** | **{r['ROP']:.0f} {b['satuan']}** |
| **Safety Stock** | **{r['Safety Stock']:.1f} {b['satuan']}** |
""".replace(",", "."))
        ui.riset_tag("RQ5 · Sec. 3.6.3 BOM · Sec. 3.6.4 EOQ/ROP/Safety Stock")

    st.markdown("<br>", unsafe_allow_html=True)
    ui.section("Pemetaan Pertanyaan Penelitian", "")
    rq = pd.DataFrame([
        ["RQ1", "Data sintetis valid (weekend/libur/cuaca)", "Tab Dataset Sintetis"],
        ["RQ2/RQ3", "Model terbaik & metrik MAE/RMSE/MAPE", "Tab Perbandingan Model"],
        ["RQ4", "Pengaruh variabel eksogen", "Tab Ablation Eksogen"],
        ["RQ5", "Akurasi & kebutuhan stok 7 hari", "Tab Formula + hal. Stok"],
        ["RQ6", "Rancangan DSS operasional UMKM", "Hal. Ringkasan/Perkiraan/Stok"],
    ], columns=["RQ", "Pertanyaan", "Lokasi di Dashboard"])
    st.dataframe(rq, use_container_width=True, hide_index=True)
