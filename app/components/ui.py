"""
components/ui.py - Tema visual dan komponen UI yang dipakai berulang.

Tema light, tanpa emoji; status disampaikan lewat warna dan label teks.
"""
import streamlit as st
from config import WARNA

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {{
  --primer:{WARNA['primer']}; --sekunder:{WARNA['sekunder']};
  --kritis:{WARNA['kritis']}; --waspada:{WARNA['waspada']}; --aman:{WARNA['aman']};
  --garis:{WARNA['garis']}; --teks:{WARNA['teks']}; --teks-lemah:{WARNA['teks_lemah']};
  --kartu:{WARNA['kartu']};
}}

html, body, [class*="css"], .stApp {{
  font-family:'Plus Jakarta Sans',sans-serif; color:var(--teks);
}}
.stApp {{ background:{WARNA['bg']}; }}
h1,h2,h3,h4 {{ font-family:'Source Serif 4',Georgia,serif; color:var(--sekunder);
  letter-spacing:-.01em; }}
.block-container {{ padding-top:1.8rem; max-width:1160px; }}

/* sidebar — teks dipaksa gelap & terbaca */
section[data-testid="stSidebar"] {{ background:var(--kartu); border-right:1px solid var(--garis); }}
section[data-testid="stSidebar"] * {{ color:var(--teks) !important; }}
section[data-testid="stSidebar"] .stRadio label {{ font-weight:600; font-size:.95rem; }}
section[data-testid="stSidebar"] .stRadio label p {{ color:var(--teks) !important; }}

/* KPI card — kartu putih kontras dgn bg abu */
.kpi {{ background:var(--kartu); border:1px solid var(--garis); border-radius:14px;
  padding:18px 20px; height:100%; box-shadow:0 1px 3px rgba(16,40,64,.07); }}
.kpi .label {{ font-size:.78rem; color:var(--teks-lemah); font-weight:700;
  text-transform:uppercase; letter-spacing:.045em; }}
.kpi .value {{ font-family:'Source Serif 4',serif; font-size:2.0rem; font-weight:700;
  color:var(--sekunder); line-height:1.1; margin-top:6px; }}
.kpi .sub {{ font-size:.83rem; color:var(--teks-lemah); margin-top:7px; }}
.kpi .accent {{ height:3px; width:32px; border-radius:3px; background:var(--primer); margin-bottom:13px; }}

/* status pill */
.pill {{ display:inline-block; padding:3px 11px; border-radius:999px;
  font-size:.74rem; font-weight:700; letter-spacing:.02em; }}
.pill.kritis  {{ background:#FBE6E9; color:var(--kritis); }}
.pill.waspada {{ background:#FBF0DE; color:var(--waspada); }}
.pill.aman    {{ background:#E2F3EC; color:var(--aman); }}

/* action card (pengganti alert emoji) */
.action {{ background:var(--kartu); border:1px solid var(--garis); border-left:4px solid;
  border-radius:11px; padding:13px 16px; margin:8px 0; box-shadow:0 1px 2px rgba(16,40,64,.04); }}
.action.kritis  {{ border-left-color:var(--kritis); }}
.action.waspada {{ border-left-color:var(--waspada); }}
.action.info    {{ border-left-color:var(--sekunder); }}
.action.aman    {{ border-left-color:var(--aman); }}
.action .judul {{ font-weight:700; color:var(--teks); font-size:.96rem; }}
.action .detail {{ color:var(--teks-lemah); font-size:.87rem; margin-top:3px; line-height:1.45; }}

/* section header */
.section {{ font-family:'Source Serif 4',serif; font-size:1.2rem; font-weight:600;
  color:var(--sekunder); margin:6px 0 2px; }}
.section-sub {{ color:var(--teks-lemah); font-size:.87rem; margin-bottom:12px; }}

/* tag riset — HANYA dipakai di halaman Validasi (untuk penguji) */
.riset {{ display:inline-block; background:#EEF3F6; color:var(--sekunder);
  border:1px solid var(--garis); border-radius:6px; padding:2px 9px;
  font-size:.72rem; font-weight:600; margin-top:8px; }}

table {{ font-size:.9rem; }}
.stDataFrame {{ border:1px solid var(--garis); border-radius:10px; }}
</style>
"""


def inject():
    st.markdown(_CSS, unsafe_allow_html=True)


def kpi(label: str, value: str, sub: str = ""):
    st.markdown(
        f'<div class="kpi"><div class="accent"></div>'
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
