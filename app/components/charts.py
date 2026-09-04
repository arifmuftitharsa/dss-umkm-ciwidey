"""
components/charts.py - Helper grafik Plotly.

Semua grafik memakai palet warna dari config.WARNA.
"""
import plotly.graph_objects as go
import pandas as pd
from config import WARNA, MODEL


_LAYOUT = dict(
    font=dict(family="Plus Jakarta Sans, sans-serif", color=WARNA["teks"], size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=30, b=10),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
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

    # rentang perkiraan (area + garis batas agar jelas terlihat)
    fig.add_trace(go.Scatter(
        x=list(future.date) + list(future.date[::-1]),
        y=list(future.yhat_upper) + list(future.yhat_lower[::-1]),
        fill="toself", fillcolor="rgba(14,138,107,.20)",
        line=dict(color="rgba(14,138,107,.45)", width=1, dash="dot"),
        hoverinfo="skip", name="Rentang perkiraan",
    ))
    # penjualan sebelumnya
    fig.add_trace(go.Scatter(
        x=history.date, y=history.quantity_sold, mode="lines",
        line=dict(color=WARNA["sekunder"], width=2), name="Penjualan sebelumnya",
        hovertemplate="%{x|%a %d %b}<br>Terjual: %{y} " + satuan + "<extra></extra>",
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
        hovertemplate="%{x|%a %d %b}<br>Perkiraan: %{y} " + satuan + "<extra></extra>",
    ))
    # penanda hari libur/event — garis tipis + TITIK KUNING di kurva perkiraan
    hol = future[future.is_holiday == 1]
    if not hol.empty:
        for _, r in hol.iterrows():
            fig.add_vline(x=r.date,
                          line=dict(color="#E0A100", width=1, dash="dash"))
        fig.add_trace(go.Scatter(
            x=hol.date, y=hol.yhat, mode="markers",
            marker=dict(size=14, color="#F4B400", symbol="circle",
                        line=dict(width=2, color="#B5731A")),
            name="Hari libur / event",
            hovertemplate="%{x|%a %d %b}<br><b>Hari libur nasional</b>"
                          "<br>Perkiraan ramai: %{y} " + satuan + "<extra></extra>",
        ))

    # penanda libur pada DATA HISTORIS (sebelum forecast) — titik kuning juga
    if "is_holiday" in history.columns:
        hol_h = history[history.is_holiday == 1]
        if not hol_h.empty:
            fig.add_trace(go.Scatter(
                x=hol_h.date, y=hol_h.quantity_sold, mode="markers",
                marker=dict(size=11, color="#F4B400", symbol="circle",
                            line=dict(width=1.5, color="#B5731A")),
                name="Libur (lampau)", showlegend=False,
                hovertemplate="%{x|%a %d %b}<br><b>Hari libur (lampau)</b>"
                              "<br>Terjual: %{y} " + satuan + "<extra></extra>",
            ))

    lay = _layout(hovermode="x unified")
    fig.update_layout(**lay, height=380, yaxis_title=f"Unit ({satuan})")
    fig.update_xaxes(**_GRID, fixedrange=True)   # matikan geser/zoom
    fig.update_yaxes(**_GRID, fixedrange=True)
    return fig


def inventory_bar(tbl: pd.DataFrame):
    """Bar stok vs ROP per bahan baku, diwarnai status. Hover per-item (closest)."""
    warna = {"Kritis": WARNA["kritis"], "Waspada": WARNA["waspada"], "Aman": WARNA["aman"]}
    sat = tbl["Satuan"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=tbl["Bahan Baku"], x=tbl["Stok"], orientation="h",
        marker_color=[warna[s] for s in tbl["Status"]],
        name="Stok saat ini", customdata=sat,
        text=tbl["Stok"], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Stok: %{x} %{customdata}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        y=tbl["Bahan Baku"], x=tbl["ROP"], mode="markers",
        marker=dict(symbol="line-ns", size=22, color=WARNA["sekunder"],
                    line=dict(width=3, color=WARNA["sekunder"])),
        name="Batas aman (ROP)", customdata=sat,
        hovertemplate="<b>%{y}</b><br>Batas aman (ROP): %{x:.0f} %{customdata}<extra></extra>",
    ))
    # penanda EOQ — garis seperti ROP tapi warna kuning emas (jumlah beli ideal)
    if "EOQ" in tbl.columns:
        fig.add_trace(go.Scatter(
            y=tbl["Bahan Baku"], x=tbl["EOQ"], mode="markers",
            marker=dict(symbol="line-ns", size=22, color="#F4B400",
                        line=dict(width=3, color="#F4B400")),
            name="Jumlah beli ideal (EOQ)", customdata=sat,
            hovertemplate="<b>%{y}</b><br>EOQ (beli sekali pesan): %{x:.0f} %{customdata}<extra></extra>",
        ))
    # hovermode 'closest' -> hanya item yang ditunjuk; fixedrange -> tak bisa digeser
    lay = _layout(hovermode="closest")
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
