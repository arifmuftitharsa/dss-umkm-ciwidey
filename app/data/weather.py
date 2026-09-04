"""
data/weather.py - Variabel eksogen masa depan: cuaca + kalender libur.

Cuaca:
  hari 1-16 : prakiraan numerik Open-Meteo Forecast API
  hari 17+  : klimatologi curah hujan bulanan Ciwidey (proksi deterministik)

Batas 16 hari adalah batas prakiraan cuaca numerik itu sendiri, bukan
keterbatasan API. Bila API gagal ATAU start_date sudah lewat dari hari
sungguhan (Open-Meteo Forecast API cuma bisa "N hari ke depan dari
sekarang", bukan tanggal sembarang), seluruh periode memakai klimatologi
— dan jejaknya dicatat lewat modul logging (lihat fetch_rainfall_forecast).

Libur: kalender libur nasional Indonesia (python-holidays), dengan panjang
window per jenis libur yang dapat diatur pemilik lewat halaman Manajemen.
"""
from __future__ import annotations
import logging
from typing import NamedTuple

import numpy as np
import pandas as pd
import requests

from config import STUDI_KASUS

logger = logging.getLogger(__name__)

LAT, LON = STUDI_KASUS["koordinat"]


class RainfallForecast(NamedTuple):
    """Hasil fetch_rainfall_forecast(): nilai curah hujan + status sumbernya.

    used_climatology bernilai True kalau ADA bagian window yang jatuh ke
    klimatologi (baik sebagian maupun seluruhnya) -- False hanya kalau
    seluruh window benar-benar dari Open-Meteo Forecast API live. Disiapkan
    untuk dikonsumsi UI pada pekerjaan Minggu 3/T-19 (belum dipakai di sana
    sekarang -- lihat core/forecasting.py dan data/record_sales.py).
    """
    values: np.ndarray
    used_climatology: bool

# Batas prakiraan numerik Open-Meteo (sifat sains cuaca, bukan keterbatasan API)
MAX_FORECAST_DAYS = 16

# Klimatologi curah hujan bulanan wilayah Ciwidey (mm), dihitung dari data
# aktual Open-Meteo Archive 2023-2025. Dipakai sebagai proksi untuk hari di
# luar jangkauan prakiraan numerik (> 16 hari).
KLIMATOLOGI_BULANAN = {
    1: 8.0, 2: 8.1, 3: 7.4, 4: 6.2, 5: 6.3, 6: 2.9,
    7: 2.2, 8: 2.3, 9: 3.3, 10: 3.7, 11: 8.2, 12: 9.0,
}


def _klimatologi(dates):
    """Curah hujan proksi dari rata-rata historis bulan ybs (deterministik)."""
    return np.array([KLIMATOLOGI_BULANAN.get(pd.Timestamp(d).month, 5.6)
                     for d in dates])


def fetch_rainfall_forecast(start_date, n_days=7) -> RainfallForecast:
    """
    Curah hujan harian n hari ke depan (mm) mulai start_date.

    Return RainfallForecast(values, used_climatology) -- lihat docstring
    kelasnya untuk arti used_climatology.

    Open-Meteo Forecast API cuma bisa menjawab "N hari ke depan dari HARI
    SUNGGUHAN sekarang" — bukan tanggal sembarang. Jadi start_date dulu
    diposisikan relatif hari sungguhan sebelum API dipanggil:

      - start_date < hari ini       : seluruhnya di masa lalu relatif hari
                                       sungguhan -> API tak bisa menjawab ini
                                       sama sekali (bukan kegagalan, memang
                                       di luar jangkauan API). Klimatologi
                                       penuh dipakai, dicatat via logger.info
                                       (kondisi ini terjadi selama T-1 belum
                                       diperbaiki, karena last_date terkunci
                                       di masa lalu; begitu T-1 selesai,
                                       start_date otomatis jadi hari ini,
                                       cabang ini otomatis tidak lagi
                                       terpakai tanpa modifikasi kode).
      - start_date >= hari ini      : window kita ada di dalam (sebagian
                                       atau seluruhnya) rentang yang bisa
                                       dijawab API. Hasil API digeser sesuai
                                       offset (start_date - hari ini)
                                       sebelum ditempel ke tanggal target.

    Hari ke-17 dst dari start_date (di luar MAX_FORECAST_DAYS) tetap
    klimatologi, sesuai batas fundamental sains cuaca.

    Bila API gagal (jaringan/HTTP/format respons), seluruh periode pakai
    klimatologi dan kegagalan dicatat via logger.warning — bukan ditelan
    senyap.
    """
    dates = pd.date_range(start_date, periods=n_days, freq="D")
    rain = _klimatologi(dates)  # default: klimatologi penuh

    today = pd.Timestamp.now().normalize()
    start = pd.Timestamp(start_date).normalize()
    offset_days = (start - today).days

    if offset_days < 0:
        logger.info(
            "fetch_rainfall_forecast: start_date %s ada di masa lalu relatif "
            "hari ini (%s) -- Open-Meteo Forecast API tak bisa menjawab "
            "tanggal itu (API ini cuma 'N hari ke depan dari sekarang'). "
            "Pakai klimatologi penuh. Kondisi ini normal selama T-1 belum "
            "diperbaiki (last_date terkunci di masa lalu).",
            start.date(), today.date(),
        )
        return RainfallForecast(np.round(rain, 1), used_climatology=True)

    # Berapa hari perlu diminta dari API supaya window [offset_days,
    # offset_days + n_days) tercakup, dibatasi jangkauan numerik API.
    request_days = min(offset_days + n_days, MAX_FORECAST_DAYS)
    n_usable = request_days - offset_days  # bagian yang relevan buat window kita
    if n_usable <= 0:
        # Seluruh window kita > MAX_FORECAST_DAYS hari dari sekarang.
        return RainfallForecast(np.round(rain, 1), used_climatology=True)

    # Kalau n_usable < n_days, sisa hari (ke-17+ dari sekarang) tetap
    # klimatologi walau API di bawah ini sukses penuh untuk bagian awal.
    used_climatology = n_usable < n_days

    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={LAT}&longitude={LON}"
            "&daily=precipitation_sum&timezone=Asia%2FJakarta"
            f"&forecast_days={request_days}"
        )
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        vals = np.nan_to_num(np.array(
            r.json()["daily"]["precipitation_sum"], dtype=float), nan=0.0)
        # vals[0] = curah hujan hari ini sungguhan; geser sesuai offset
        # supaya vals[offset_days] cocok dengan dates[0] (= start_date).
        window_vals = vals[offset_days:offset_days + n_usable]
        rain[:len(window_vals)] = window_vals
    except (requests.RequestException, KeyError, ValueError, TypeError) as e:
        logger.warning(
            "fetch_rainfall_forecast: gagal ambil data Open-Meteo (%s: %s) "
            "-- pakai klimatologi sebagai cadangan.",
            type(e).__name__, e,
        )
        used_climatology = True  # seluruh window jatuh ke klimatologi

    return RainfallForecast(np.round(rain, 1), used_climatology)


def _clean_name(nama: str) -> str:
    """Buang sufiks (perkiraan)/(estimated) & ambil 1 nama bila gabungan."""
    import re
    nama = (nama or "").split(";")[0]
    nama = re.sub(r"\s*\((perkiraan|estimated)\)\s*", "", nama, flags=re.I)
    return nama.strip()


# Peta normalisasi nama libur -> Indonesia kanonik (tak bergantung versi library).
# Key di-lowercase. Mencakup varian Inggris & Indonesia agar konsisten.
_HOLIDAY_ID = {
    "new year's day": "Tahun Baru Masehi",
    "tahun baru masehi": "Tahun Baru Masehi",
    "isra' and mi'raj": "Isra Mikraj Nabi Muhammad",
    "isra and mi'raj": "Isra Mikraj Nabi Muhammad",
    "isra mikraj nabi muhammad": "Isra Mikraj Nabi Muhammad",
    "lunar new year": "Tahun Baru Imlek",
    "tahun baru imlek": "Tahun Baru Imlek",
    "day of silence": "Hari Suci Nyepi",
    "hari suci nyepi": "Hari Suci Nyepi",
    "good friday": "Wafat Yesus Kristus",
    "wafat yesus kristus": "Wafat Yesus Kristus",
    "easter sunday": "Kebangkitan Yesus Kristus",
    "kebangkitan yesus kristus": "Kebangkitan Yesus Kristus",
    "eid al-fitr": "Hari Raya Idul Fitri",
    "hari raya idul fitri": "Hari Raya Idul Fitri",
    "eid al-fitr second day": "Hari Kedua Idul Fitri",
    "hari kedua dari hari raya idul fitri": "Hari Kedua Idul Fitri",
    "international labor day": "Hari Buruh Internasional",
    "hari buruh internasional": "Hari Buruh Internasional",
    "ascension day": "Kenaikan Yesus Kristus",
    "kenaikan yesus kristus": "Kenaikan Yesus Kristus",
    "vesak day": "Hari Raya Waisak",
    "hari raya waisak": "Hari Raya Waisak",
    "pancasila day": "Hari Lahir Pancasila",
    "hari lahir pancasila": "Hari Lahir Pancasila",
    "eid al-adha": "Hari Raya Idul Adha",
    "hari raya idul adha": "Hari Raya Idul Adha",
    "islamic new year": "Tahun Baru Islam (1 Muharram)",
    "tahun baru islam": "Tahun Baru Islam (1 Muharram)",
    "independence day": "Hari Kemerdekaan RI",
    "hari kemerdekaan republik indonesia": "Hari Kemerdekaan RI",
    "prophet's birthday": "Maulid Nabi Muhammad",
    "maulid nabi muhammad": "Maulid Nabi Muhammad",
    "christmas day": "Hari Raya Natal",
    "hari raya natal": "Hari Raya Natal",
    "general election day": "Hari Pemilihan Umum",
    "hari pemilihan unum": "Hari Pemilihan Umum",
    "hari pemilihan umum": "Hari Pemilihan Umum",
    "local election day": "Hari Pemilihan Kepala Daerah",
    "hari pemilihan kepala daerah": "Hari Pemilihan Kepala Daerah",
}


def normalize_holiday_name(nama: str) -> str:
    """Kembalikan nama libur dalam Bahasa Indonesia kanonik."""
    c = _clean_name(nama)
    return _HOLIDAY_ID.get(c.lower(), c)


def get_holidays_map(years):
    """Dict {tanggal: nama_libur_indonesia_bersih} untuk klasifikasi jenis libur."""
    try:
        import holidays
        try:
            h = holidays.Indonesia(years=list(years), language="id")
        except Exception:
            h = holidays.Indonesia(years=list(years))
        return {tgl: normalize_holiday_name(nama) for tgl, nama in h.items()}
    except Exception:
        return {}


# Window per JENIS libur (H- sebelum, H+ sesudah). Libur besar lebih panjang.
WINDOW_PER_LIBUR = {
    "idul fitri": (-2, 7),   # Lebaran: arus mudik-balik panjang
    "lebaran":    (-2, 7),
    "natal":      (-2, 3),   # Nataru
    "tahun baru": (-1, 2),
    "_default":   (-1, 2),   # libur nasional biasa (asumsi konservatif Sec 3.2.2)
}


def _window_for(nama_libur: str):
    """
    Window (lo, hi) untuk jenis libur. Dibaca dari DATABASE (editable pemilik),
    fallback ke default bawaan bila DB tak tersedia.
    """
    n = (nama_libur or "").lower()
    try:
        from data import store
        cfg = store.get_window_config()   # {jenis: (h_minus, h_plus)}
    except Exception:
        cfg = {"(default)": (1, 2)}
    # 1) cocok nama PERSIS (tiap libur bisa punya window sendiri)
    if n in cfg:
        hm, hp = cfg[n]
        return (-hm, hp)
    # 2) cocok substring (kata kunci, mis. "idul fitri")
    for kunci, (hm, hp) in cfg.items():
        if kunci != "(default)" and kunci in n:
            return (-hm, hp)
    # 3) default
    hm, hp = cfg.get("(default)", (1, 2))
    return (-hm, hp)


def future_exogenous(start_date, n_days=7):
    """
    Bangun DataFrame eksogen untuk n hari ke depan mulai start_date.
    Kolom: date, is_weekend, is_holiday, holiday_window (label), rainfall_mm.
    Window libur kini PER-JENIS (Lebaran lebih panjang dari libur biasa).

    Return (DataFrame, used_climatology) -- used_climatology diteruskan
    apa adanya dari fetch_rainfall_forecast(), lihat RainfallForecast.
    """
    dates = pd.date_range(start_date, periods=n_days, freq="D")
    years = sorted({d.year for d in dates} | {(start_date.year - 1),
                                               (start_date.year + 1)})
    hmap = get_holidays_map(years)            # {tanggal: nama}
    hols = set(hmap.keys())

    is_weekend = (dates.dayofweek >= 5).astype(int)
    is_holiday = np.array([1 if d.date() in hols else 0 for d in dates])

    def window_label(d):
        d0 = d.date()
        if d0 in hols:
            return "H"
        # cek libur terdekat dengan window sesuai JENIS libur tsb
        for off in range(1, 8):
            past = (d - pd.Timedelta(days=off)).date()
            futr = (d + pd.Timedelta(days=off)).date()
            if past in hols:
                _, hi = _window_for(hmap.get(past, ""))
                if off <= hi:
                    return f"H+{off}"
            if futr in hols:
                lo, _ = _window_for(hmap.get(futr, ""))
                if off <= abs(lo):
                    return f"H-{off}"
        return "---"

    window = [window_label(d) for d in dates]
    rainfall = fetch_rainfall_forecast(start_date, n_days)

    df = pd.DataFrame({
        "date": dates,
        "is_weekend": is_weekend,
        "is_holiday": is_holiday,
        "holiday_window": window,
        "rainfall_mm": rainfall.values,
    })
    return df, rainfall.used_climatology


def list_holidays_with_window(years):
    """
    Daftar hari libur nasional beserta window efektifnya (untuk transparansi UI).
    """
    hmap = get_holidays_map(years)
    rows = []
    for tgl, nama in sorted(hmap.items()):
        lo, hi = _window_for(nama)
        rows.append({
            "Tanggal": pd.Timestamp(tgl).strftime("%Y-%m-%d"),
            "Hari Libur Nasional": nama,
            "Efek mulai": f"H{lo} ({abs(lo)} hari sebelum libur)",
            "Efek sampai": f"H+{hi} ({hi} hari sesudah libur)",
        })
    return pd.DataFrame(rows)
