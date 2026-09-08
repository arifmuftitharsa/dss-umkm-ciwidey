"""
components/ui.py - Tema visual dan komponen UI yang dipakai berulang.

Tema light, tanpa emoji; status disampaikan lewat warna dan label teks.
"""
import streamlit as st
import pandas as pd
from config import WARNA

# Nama hari/bulan Indonesia -- mapping manual, BUKAN locale.setlocale("id_ID"),
# karena locale itu sering tak terpasang di server/Windows (bisa LookupError
# saat deploy, melanggar fail-fast/reproduksibilitas). strftime()/Plotly
# hover default-nya Inggris (Saturday, Sep) -- dipakai di semua tempat yang
# menampilkan tanggal ke pengguna (Rincian per Hari, tabel bahan baku, hover
# grafik).
_HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
_BULAN_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
             "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def tanggal_id(dt, hari_penuh: bool = True) -> str:
    """Format tanggal Bahasa Indonesia, mis. 'Senin, 05 Sep' atau 'Sen 05 Sep'."""
    dt = pd.Timestamp(dt)
    hari = _HARI_ID[dt.dayofweek]
    bulan = _BULAN_ID[dt.month - 1]
    if hari_penuh:
        return f"{hari}, {dt.day:02d} {bulan}"
    return f"{hari[:3]} {dt.day:02d} {bulan}"


def _tint(hex_color: str, alpha: float) -> str:
    """hex '#RRGGBB' -> rgba() CSS, dihitung dari token WARNA. BUKAN hardcode
    tint terpisah -- bug Tahap 2 (rgba hijau lama di charts.py) berulang di
    sini: background pill status dulu di-hex manual cocok warna kritis/
    waspada/aman LAMA, terlewat saat token ganti. Dihitung ulang tiap kali
    supaya otomatis ikut kalau token berubah lagi nanti."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {{
  --primer:{WARNA['primer']}; --sekunder:{WARNA['sekunder']}; --aksen:{WARNA['aksen']};
  --kritis:{WARNA['kritis']}; --waspada:{WARNA['waspada']}; --aman:{WARNA['aman']};
  --garis:{WARNA['garis']}; --teks:{WARNA['teks']}; --teks-lemah:{WARNA['teks_lemah']};
  --kartu:{WARNA['kartu']}; --surface:{WARNA['surface']};
}}

html, body, [class*="css"], .stApp {{
  font-family:'Plus Jakarta Sans',sans-serif; color:var(--teks);
}}
.stApp {{ background:{WARNA['bg']}; }}
h1,h2,h3,h4 {{ font-family:'Source Serif 4',Georgia,serif; color:var(--teks);
  letter-spacing:-.01em; }}
.block-container {{ padding-top:1.8rem; max-width:1160px; }}

/* sidebar -- surface (beda halus dari bg putih konten), teks dipaksa gelap & terbaca */
section[data-testid="stSidebar"] {{ background:var(--surface); border-right:1px solid var(--garis); }}
section[data-testid="stSidebar"] * {{ color:var(--teks) !important; }}

/* sidebar-flex -- satu kolom flex membungkus logo+info+watermark. min-height
   perkiraan tinggi viewport dikurangi navigasi bawaan st.navigation di atasnya
   (4 halaman -> diukur ~255px lewat DOM saat testing) supaya watermark
   (margin-top:auto) terdorong ke dasar sidebar tanpa celah kosong janggal,
   TANPA position:fixed yang dulu lepas dari isi di atasnya (akar masalah
   "sidebar kosong"). Dikurangi 280px (sedikit lebih besar dari 255px terukur)
   supaya ada margin aman, watermark tak terpotong di viewport umum. */
.sidebar-flex {{ display:flex; flex-direction:column; min-height:calc(100vh - 280px); }}
.sidebar-info {{ background:var(--kartu); border:1px solid var(--garis);
  border-left:3px solid var(--primer); border-radius:6px; padding:14px 16px;
  font-size:.78rem; line-height:1.6; }}
.sidebar-watermark {{ margin-top:auto; padding-top:1rem; font-size:.7rem;
  color:var(--teks-lemah); }}

/* KPI card -- border kiri berwarna (konsisten dgn action-card), TANPA shadow/radius
   besar seragam (hindari pola "SaaS-card kit"). Label sentence case, bukan ALL-CAPS. */
.kpi {{ background:var(--kartu); border:1px solid var(--garis); border-left:3px solid var(--primer);
  border-radius:6px; padding:16px 18px; height:100%; }}
.kpi .label {{ font-size:.83rem; color:var(--teks-lemah); font-weight:600; }}
.kpi .value {{ font-family:'Source Serif 4',serif; font-size:2.0rem; font-weight:700;
  color:var(--teks); line-height:1.1; margin-top:6px; }}
.kpi .sub {{ font-size:.83rem; color:var(--teks-lemah); margin-top:7px; }}

/* status pill */
.pill {{ display:inline-block; padding:3px 11px; border-radius:999px;
  font-size:.74rem; font-weight:700; letter-spacing:.02em; }}
.pill.kritis  {{ background:{_tint(WARNA['kritis'], .12)}; color:var(--kritis); }}
.pill.waspada {{ background:{_tint(WARNA['waspada'], .12)}; color:var(--waspada); }}
.pill.aman    {{ background:{_tint(WARNA['aman'], .12)}; color:var(--aman); }}

/* action card (pengganti alert emoji) -- radius kecil konsisten dgn KPI, tanpa shadow */
.action {{ background:var(--kartu); border:1px solid var(--garis); border-left:3px solid;
  border-radius:6px; padding:13px 16px; margin:8px 0; }}
.action.kritis  {{ border-left-color:var(--kritis); }}
.action.waspada {{ border-left-color:var(--waspada); }}
.action.info    {{ border-left-color:var(--aksen); }}
.action.aman    {{ border-left-color:var(--aman); }}
.action .judul {{ font-weight:700; color:var(--teks); font-size:.96rem; }}
.action .detail {{ color:var(--teks-lemah); font-size:.87rem; margin-top:3px; line-height:1.45; }}

/* section header -- sentence case, tanpa separator titik tengah */
.section {{ font-family:'Source Serif 4',serif; font-size:1.2rem; font-weight:600;
  color:var(--teks); margin:6px 0 2px; }}
.section-sub {{ color:var(--teks-lemah); font-size:.87rem; margin-bottom:12px; }}

/* tag riset -- dead code sisa halaman Validasi (dihapus T-10), dibiarkan di luar
   scope Tahap 1 (bukan bagian redesain, murni CSS mati tak terpanggil) */
.riset {{ display:inline-block; background:#EEF3F6; color:var(--teks);
  border:1px solid var(--garis); border-radius:6px; padding:2px 9px;
  font-size:.72rem; font-weight:600; margin-top:8px; }}

table {{ font-size:.9rem; }}
.stDataFrame {{ border:1px solid var(--garis); border-radius:8px; }}

/* tabel HTML custom (to_html manual, mis. tabel status pill -- st.dataframe()
   TAK bisa render HTML/warna per sel dengan mudah, jadi tabel ini tetap HTML
   mentah, bukan diganti). Dibungkus .tabel-scroll untuk scroll horizontal di
   mobile (tabel HTML lepas dari mekanisme resize/scroll otomatis st.dataframe). */
.tabel-scroll {{ overflow-x:auto; border:1px solid var(--garis); border-radius:8px; }}
.tabel-scroll table {{ border-collapse:collapse; width:100%; margin:0; }}
.tabel-scroll table, .tabel-scroll th, .tabel-scroll td {{ border:none; }}
.tabel-scroll th {{ text-align:left; padding:10px 14px; background:var(--surface);
  color:var(--teks-lemah); font-weight:600; font-size:.83rem;
  border-bottom:1px solid var(--garis); white-space:nowrap; }}
.tabel-scroll td {{ padding:9px 14px; border-bottom:1px solid var(--garis);
  white-space:nowrap; }}
.tabel-scroll tr:last-child td {{ border-bottom:none; }}

/* --- RESPONSIF -- breakpoint tablet/mobile. st.columns() Streamlit defaultnya
   selalu flex-row (berdampingan) walau layar sempit; dipaksa flex-column di
   bawah 768px supaya kartu KPI dkk ditumpuk, bukan berjejal sempit di HP. */
@media (max-width: 1023px) {{
  .block-container {{ padding-left:1rem; padding-right:1rem; max-width:100%; }}
}}
@media (max-width: 767px) {{
  .block-container {{ padding-top:1rem; padding-left:.75rem; padding-right:.75rem; }}
  [data-testid="stHorizontalBlock"] {{ flex-direction:column; }}
  [data-testid="stHorizontalBlock"] > div {{ width:100% !important; flex:1 1 100% !important; }}
  .kpi {{ padding:14px 16px; }}
  .kpi .value {{ font-size:1.7rem; }}
  h2 {{ font-size:1.4rem; }}
}}
</style>
"""


def inject():
    st.markdown(_CSS, unsafe_allow_html=True)


def kpi(label: str, value: str, sub: str = ""):
    """Kartu KPI -- border kiri berwarna menandai kartu (bukan shadow/accent-bar
    terpisah), konsisten dgn pola action-card. Signature tak berubah dari
    sebelumnya supaya views/ pemanggil tak perlu disentuh (Tahap 1)."""
    st.markdown(
        f'<div class="kpi">'
        f'<div class="label">{label}</div><div class="value">{value}</div>'
        f'<div class="sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def pill(status: str) -> str:
    cls = {"Kritis": "kritis", "Waspada": "waspada", "Aman": "aman"}.get(status, "aman")
    teks = {"Kritis": "Segera beli", "Waspada": "Perhatikan", "Aman": "Aman"}.get(status, status)
    return f'<span class="pill {cls}">{teks}</span>'


def action(judul: str, detail: str = "", level: str = "info"):
    """Kartu aksi tanpa emoji — severity lewat warna garis kiri + label."""
    d = f'<div class="detail">{detail}</div>' if detail else ""
    st.markdown(
        f'<div class="action {level}"><div class="judul">{judul}</div>{d}</div>',
        unsafe_allow_html=True,
    )


def section(title: str, sub: str = ""):
    st.markdown(f'<div class="section">{title}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


def riset_tag(text: str):
    """Penanda section skripsi — HANYA untuk halaman Validasi (penguji)."""
    st.markdown(f'<span class="riset">{text}</span>', unsafe_allow_html=True)
