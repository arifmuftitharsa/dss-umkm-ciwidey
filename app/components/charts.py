"""
components/charts.py - Helper grafik Plotly.

Semua grafik memakai palet warna dari config.WARNA.
"""
import plotly.graph_objects as go
import pandas as pd
from config import WARNA, MODEL
from . import ui

_TICKFORMAT_TGL = "%d/%m"  # sumbu-x numerik (hindari nama bulan Inggris
                           # Plotly, d3-time-format-nya tak punya locale ID)


_LAYOUT = dict(
    font=dict(family="Plus Jakarta Sans, sans-serif", color=WARNA["teks"], size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=30, b=10),
    hovermode="x unified",
    showlegend=False,  # Tahap B: legend Plotly bawaan dimatikan total,
                       # diganti ui.legend() HTML custom (swatch rapi,
                       # konsisten tipografi sistem desain -- lihat views/).
)
_GRID = dict(showgrid=True, gridcolor=WARNA["garis"], zeroline=False)


def _layout(**override):
    """Salin _LAYOUT lalu timpa sebagian key (mis. hovermode) tanpa duplikasi."""
    lay = dict(_LAYOUT)
    lay.update(override)
    return lay


def forecast_chart(history: pd.DataFrame, future: pd.DataFrame, satuan: str):
    """Garis penjualan historis + perkiraan 7 hari + rentang perkiraan + penanda libur."""
    fig = go.Figure()

    # Label tanggal Bahasa Indonesia untuk hover -- Plotly hovertemplate
    # "%{x|%a %d %b}" defaultnya render nama hari/bulan Inggris (d3-time-format
    # tak punya locale ID bawaan), jadi dibangun manual lewat customdata.
    hist_label = [ui.tanggal_id(d, hari_penuh=False) for d in history.date]
    fut_label = [ui.tanggal_id(d, hari_penuh=False) for d in future.date]

    # rentang perkiraan (area + garis batas agar jelas terlihat)
    fig.add_trace(go.Scatter(
        x=list(future.date) + list(future.date[::-1]),
        y=list(future.yhat_upper) + list(future.yhat_lower[::-1]),
        fill="toself", fillcolor=ui.tint(WARNA["primer"], .20),
        line=dict(color=ui.tint(WARNA["primer"], .45), width=1, dash="dot"),
        hoverinfo="skip", name="Rentang perkiraan",
    ))
    # penjualan sebelumnya
    fig.add_trace(go.Scatter(
        x=history.date, y=history.quantity_sold, mode="lines",
        line=dict(color=WARNA["sekunder"], width=2), name="Penjualan sebelumnya",
        customdata=hist_label,
        hovertemplate="%{customdata}<br>Terjual: %{y} " + satuan + "<extra></extra>",
    ))
    # jembatan aktual->perkiraan -- hanya kalau ada riwayat. Produk baru
    # tanpa penjualan sebelumnya (T-4) punya history kosong: tak ada apa
    # pun untuk disambung, itu kebenaran (belum pernah terjual), bukan
    # kekurangan tampilan yang perlu ditambal dengan data karangan.
    if not history.empty:
        bridge_x = [history.date.iloc[-1], future.date.iloc[0]]
        bridge_y = [history.quantity_sold.iloc[-1], future.yhat.iloc[0]]
        fig.add_trace(go.Scatter(x=bridge_x, y=bridge_y, mode="lines",
                                 line=dict(color=WARNA["primer"], width=2, dash="dot"),
                                 showlegend=False, hoverinfo="skip"))
    # perkiraan
    fig.add_trace(go.Scatter(
        x=future.date, y=future.yhat, mode="lines+markers",
        line=dict(color=WARNA["primer"], width=3), marker=dict(size=8),
        name="Perkiraan 7 hari",
        customdata=fut_label,
        hovertemplate="%{customdata}<br>Perkiraan: %{y} " + satuan + "<extra></extra>",
    ))
    # penanda hari libur/event — garis tipis + TITIK KUNING di kurva perkiraan
    hol = future[future.is_holiday == 1]
    if not hol.empty:
        hol_label = [ui.tanggal_id(d, hari_penuh=False) for d in hol.date]
        for _, r in hol.iterrows():
            fig.add_vline(x=r.date,
                          line=dict(color="#E0A100", width=1, dash="dash"))
        fig.add_trace(go.Scatter(
            x=hol.date, y=hol.yhat, mode="markers",
            marker=dict(size=14, color="#F4B400", symbol="circle",
                        line=dict(width=2, color="#B5731A")),
            name="Hari libur / event",
            customdata=hol_label,
            hovertemplate="%{customdata}<br><b>Hari libur nasional</b>"
                          "<br>Perkiraan ramai: %{y} " + satuan + "<extra></extra>",
        ))

    # penanda libur pada DATA HISTORIS (sebelum forecast) — titik kuning juga
    if "is_holiday" in history.columns:
        hol_h = history[history.is_holiday == 1]
        if not hol_h.empty:
            hol_h_label = [ui.tanggal_id(d, hari_penuh=False) for d in hol_h.date]
            fig.add_trace(go.Scatter(
                x=hol_h.date, y=hol_h.quantity_sold, mode="markers",
                marker=dict(size=11, color="#F4B400", symbol="circle",
                            line=dict(width=1.5, color="#B5731A")),
                name="Libur (lampau)", showlegend=False,
                customdata=hol_h_label,
                hovertemplate="%{customdata}<br><b>Hari libur (lampau)</b>"
                              "<br>Terjual: %{y} " + satuan + "<extra></extra>",
            ))

    # height 400 -- rangeselector (tombol preset, di atas plot) butuh ruang
    # ekstra dibanding versi tanpa kontrol tambahan (380), tapi lebih pendek
    # dari versi rangeslider (460) yang sudah dihapus (Arif: kurang jelas
    # fungsinya). margin.t dinaikkan supaya baris tombol tak mepet legend.
    lay = _layout(hovermode="x unified", margin=dict(l=10, r=10, t=50, b=10))
    fig.update_layout(**lay, height=400, yaxis_title=f"Unit ({satuan})")
    # Tahap B: zoom sumbu-x DIAKTIFKAN (fixedrange=False) -- pengguna bisa
    # drag-select memperbesar area padat untuk lihat detail tanggal harian
    # (riwayat 90 hari + horizon bikin tick otomatis Plotly jadi ~2 mingguan,
    # keluhan "rentang waktu tak bisa dibuat detail"). Sumbu-y TETAP terkunci
    # supaya proporsi jumlah unit tak berubah-ubah saat zoom-x, mencegah
    # kesan menyesatkan (grafik "melonjak" cuma karena rescale otomatis).
    #
    # rangeselector (tombol preset "7/30 Hari Terakhir", "Semua Data") GANTI
    # rangeslider bawah -- Arif: rangeslider kurang jelas fungsinya utk
    # pengguna awam (perlu paham drag). Tombol klik langsung, pola familiar
    # (mirip filter rentang di aplikasi lain), berdampingan dgn drag-select
    # zoom yang sudah ada (tombol pilih rentang PASTI, drag untuk detail
    # bebas -- dua cara saling melengkapi, bukan saling gantikan).
    #
    # font.size title dinaikkan 13(bawaan)->16 -- perbaikan T-lanjutan:
    # "Tanggal" pada 13-14px tampak seperti "Tanqqal" (kluster huruf ganda
    # "gg" mengecil jadi ambigu di font Plus Jakarta Sans ukuran kecil).
    # Dikonfirmasi lewat inspeksi DOM SVG (data-unformatted="Tanggal" --
    # data/teks sudah benar sejak awal, murni masalah keterbacaan ukuran,
    # BUKAN tumpang tindih posisi dengan elemen lain seperti dugaan awal).
    fig.update_xaxes(
        **_GRID, fixedrange=False, tickformat=_TICKFORMAT_TGL,
        title=dict(text="Tanggal", font=dict(size=16)),
        rangeselector=dict(
            buttons=[
                dict(count=7, label="7 Hari Terakhir", step="day", stepmode="backward"),
                dict(count=30, label="30 Hari Terakhir", step="day", stepmode="backward"),
                dict(step="all", label="Semua Data"),
            ],
            bgcolor=WARNA["surface"], activecolor=ui.tint(WARNA["primer"], .25),
            font=dict(size=12, color=WARNA["teks"]),
        ),
    )
    fig.update_yaxes(**_GRID, fixedrange=True)
    return fig


def inventory_bar(tbl: pd.DataFrame):
    """Bar stok vs ROP per bahan baku, diwarnai status. Hover per-item (closest)."""
    # Tahap B: warna bar pakai token *_bar (muted) -- BUKAN kritis/waspada/
    # aman biasa (itu saturasi penuh, dipakai pill/teks). Area bar besar
    # dengan saturasi penuh "berteriak" bentrok navy tenang komponen lain.
    warna = {"Kritis": WARNA["kritis_bar"], "Waspada": WARNA["waspada_bar"],
            "Aman": WARNA["aman_bar"]}
    sat = tbl["Satuan"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=tbl["Bahan Baku"], x=tbl["Stok"], orientation="h",
        marker_color=[warna[s] for s in tbl["Status"]],
        name="Stok saat ini", customdata=sat,
        hovertemplate="<b>%{y}</b><br>Stok: %{x} %{customdata}<extra></extra>",
    ))
    # Label angka stok dipindah dari text=/textposition="outside" bawaan Bar
    # ke fig.add_annotation() per baris -- BUKAN sekadar tambal 2 baris yang
    # kebetulan bentrok (Tepung Terigu, Stroberi Segar). Akar masalahnya
    # struktural: Plotly render SVG per LAPISAN TIPE trace (semua bar dulu,
    # baru semua scatter), bukan urutan add_trace() -- jadi marker ROP/EOQ
    # (scatter, ditambah setelah bar) SELALU tergambar di ATAS label teks
    # bar, untuk kombinasi data apa pun di masa depan, bukan cuma kasus ini.
    # Annotation Plotly render di layer PALING ATAS (di atas bar & scatter
    # keduanya) -- perbaikan pada akar (Open/Closed: aman utk data baru),
    # bukan cuma pada gejala yang kebetulan ketahuan.
    for _, row in tbl.iterrows():
        fig.add_annotation(
            x=row["Stok"], y=row["Bahan Baku"], text=str(row["Stok"]),
            showarrow=False, xanchor="left", xshift=6,
            font=dict(size=13, color=WARNA["teks"]),
            bgcolor="rgba(255,255,255,.75)",
        )
    # Marker ROP: WARNA['teks'] (nyaris hitam) -- bukan sekunder abu-abu lagi,
    # kontras rendah di atas bar (terutama bar pendek: Mentega, Tepung
    # Terigu). width/size dinaikkan supaya tetap kelihatan di bar sependek
    # apapun.
    fig.add_trace(go.Scatter(
        y=tbl["Bahan Baku"], x=tbl["ROP"], mode="markers",
        marker=dict(symbol="line-ns", size=26, color=WARNA["teks"],
                    line=dict(width=4, color=WARNA["teks"])),
        name="Batas aman (ROP)", customdata=sat,
        hovertemplate="<b>%{y}</b><br>Batas aman (ROP): %{x:.0f} %{customdata}<extra></extra>",
    ))
    # penanda EOQ — garis seperti ROP tapi warna kuning emas (jumlah beli ideal)
    if "EOQ" in tbl.columns:
        fig.add_trace(go.Scatter(
            y=tbl["Bahan Baku"], x=tbl["EOQ"], mode="markers",
            marker=dict(symbol="line-ns", size=26, color="#F4B400",
                        line=dict(width=4, color="#F4B400")),
            name="Jumlah beli ideal (EOQ)", customdata=sat,
            hovertemplate="<b>%{y}</b><br>EOQ (beli sekali pesan): %{x:.0f} %{customdata}<extra></extra>",
        ))
    # hovermode 'closest' -> hanya item yang ditunjuk; fixedrange -> tak bisa
    # digeser (sumbu x di sini JUMLAH, bukan tanggal -- keputusan zoom
    # Tahap B soal "detail rentang waktu" tak relevan untuk chart ini).
    # margin r=40 (bukan 10 default) -- beri ruang napas label angka
    # "outside" yang dulu mepet ke ujung bar.
    lay = _layout(hovermode="closest", margin=dict(l=10, r=40, t=30, b=10))
    fig.update_layout(**lay, height=330, xaxis_title="Jumlah (satuan masing-masing)")
    fig.update_xaxes(**_GRID, fixedrange=True)
    fig.update_yaxes(showgrid=False, fixedrange=True)
    return fig


def model_compare_bar(metrics: pd.DataFrame, horizon: str = "H+7"):
    """Bar MAPE per model untuk satu horizon."""
    d = metrics[metrics.Horizon == horizon].copy()
    fig = go.Figure(go.Bar(
        x=d["Model"], y=d["MAPE (%)"],
        marker_color=[MODEL[k]["warna"] for k in d["_key"]],
        text=d["MAPE (%)"], textposition="outside",
    ))
    fig.update_layout(**_LAYOUT, height=320, yaxis_title="MAPE (%)",
                      title=f"Perbandingan MAPE antar model — horizon {horizon}")
    fig.update_xaxes(showgrid=False, fixedrange=True)
    fig.update_yaxes(**_GRID, fixedrange=True)
    return fig


def ablation_chart(abl: pd.DataFrame):
    fig = go.Figure(go.Scatter(
        x=abl["Skenario"], y=abl["MAPE (%)"], mode="lines+markers+text",
        line=dict(color=WARNA["primer"], width=3), marker=dict(size=11),
        text=abl["MAPE (%)"], textposition="top center",
    ))
    fig.update_layout(**_LAYOUT, height=300, yaxis_title="MAPE (%)",
                      title="Ablation study — kontribusi variabel eksogen")
    fig.update_xaxes(showgrid=False, fixedrange=True, title="Skenario (A→D, eksogen makin lengkap)")
    fig.update_yaxes(**_GRID, fixedrange=True)
    return fig


def weekly_pattern(df, product_id):
    """Rata-rata permintaan per hari-dalam-minggu (memvalidasi weekly seasonality)."""
    s = df[df.product_id == product_id].copy()
    s["dow"] = pd.to_datetime(s.date).dt.dayofweek
    nama = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    g = s.groupby("dow")["quantity_sold"].mean().reindex(range(7))
    fig = go.Figure(go.Bar(
        x=nama, y=g.values,
        marker_color=[WARNA["primer"] if i >= 5 else WARNA["sekunder"] for i in range(7)],
    ))
    fig.update_layout(**_LAYOUT, height=280, yaxis_title="Rata-rata unit/hari",
                      title="Pola mingguan (akhir pekan = hijau)")
    fig.update_xaxes(showgrid=False, fixedrange=True)
    fig.update_yaxes(**_GRID, fixedrange=True)
    return fig
