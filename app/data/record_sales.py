"""
data/record_sales.py - Pencatatan penjualan harian oleh pemilik.

Penjualan aktual ditulis ke historis_penjualan.csv; kolom eksogen (weekend,
libur, window, cuaca) diisi otomatis dari kalender dan data cuaca.

Aturan integritas data - fitur lag/rolling butuh deret harian yang kontinu,
jadi pencatatan harus maju satu hari dari data terakhir, tanpa jeda tanggal
dan tanpa menimpa tanggal yang sudah ada.

Catatan: mencatat penjualan tidak melatih ulang model. Bobot model tetap dari
hasil pelatihan; yang berubah hanya lag/rolling yang dibaca saat forecast
berikutnya. Pelatihan ulang berkala adalah pengembangan lanjutan (Bab V).
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

from data import weather

_CSV_PATH = Path(__file__).resolve().parent / "historis_penjualan.csv"


def last_date_of(product_id: str):
    """Tanggal terakhir yang memiliki data untuk produk ini."""
    df = pd.read_csv(_CSV_PATH, usecols=["date", "product_id"], parse_dates=["date"])
    sub = df[df.product_id == product_id]
    return None if sub.empty else sub["date"].max()


def next_valid_date(product_id: str):
    """Satu-satunya tanggal yang boleh dicatat berikutnya (hari setelah terakhir)."""
    last = last_date_of(product_id)
    return None if last is None else (last + pd.Timedelta(days=1))


def record_one(product_id: str, product_name: str, tanggal, qty: int):
    """
    Catat 1 penjualan. Hanya menerima tanggal = (data terakhir + 1 hari).
    Mengembalikan (berhasil: bool, pesan: str).
    """
    tanggal = pd.Timestamp(tanggal).normalize()
    last = last_date_of(product_id)

    if last is None:
        return False, f"Belum ada data dasar untuk {product_id}. Buat historis dulu."

    nxt = last + pd.Timedelta(days=1)

    # tolak tanggal yang sudah ada / masa lalu
    if tanggal <= last:
        return False, (f"❌ Tidak bisa mencatat {tanggal.date()} — sudah memiliki "
                       f"data (data terakhir: {last.date()}). Pencatatan hanya "
                       f"boleh maju ke depan, tidak menimpa masa lalu.")

    # tolak lompatan tanggal (gap) -> mencegah missing value
    if tanggal > nxt:
        jeda = (tanggal - nxt).days + 1
        return False, (f"❌ Ada jeda {jeda} hari. Data harus berurutan tanpa "
                       f"lompatan agar perkiraan tetap valid. Tanggal yang harus "
                       f"dicatat berikutnya: {nxt.date()}.")

    # tanggal == nxt -> valid
    # used_climatology: disiapkan untuk Minggu 3/T-19, belum dipakai di sini
    # -- lihat data/weather.py.
    fx_df, used_climatology = weather.future_exogenous(tanggal, 1)
    fx = fx_df.iloc[0]
    baris = {
        "date": tanggal.strftime("%Y-%m-%d"),
        "product_id": product_id,
        "product_name": product_name,
        "qty_sold": int(qty),
        "is_weekend": int(fx.is_weekend),
        "is_holiday": int(fx.is_holiday),
        "holiday_window": fx.holiday_window,
        "rainfall_mm": round(float(fx.rainfall_mm), 1),
    }
    pd.DataFrame([baris]).to_csv(_CSV_PATH, mode="a", header=False, index=False)

    # reset cache history agar forecast langsung pakai data baru
    try:
        import core.forecasting as fc
        fc._HIST = None
    except Exception:
        pass

    return True, (f"✓ Tercatat: {product_name}, {tanggal.date()}, {qty} unit. "
                  f"Perkiraan kini maju mulai {(tanggal + pd.Timedelta(days=1)).date()}.")


def last_records(product_id: str = None, n: int = 8) -> pd.DataFrame:
    """n catatan terakhir untuk ditampilkan (tanggal tanpa jam)."""
    df = pd.read_csv(_CSV_PATH, parse_dates=["date"])
    if product_id:
        df = df[df.product_id == product_id]
    out = df.sort_values("date").tail(n)[
        ["date", "product_id", "qty_sold", "is_holiday", "holiday_window"]].copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")   # buang 00:00:00
    out = out.rename(columns={"date": "Tanggal", "product_id": "Produk",
                              "qty_sold": "Terjual", "is_holiday": "Libur",
                              "holiday_window": "Window"})
    return out


# Tanggal akhir data sintetis dasar (sebelum ini = data dasar, tak boleh diedit)
BASE_END = pd.Timestamp("2025-12-31")


def manual_records(product_id: str) -> pd.DataFrame:
    """Catatan yang ditambahkan manual (setelah data dasar) — boleh diedit/hapus."""
    df = pd.read_csv(_CSV_PATH, parse_dates=["date"])
    df = df[(df.product_id == product_id) & (df.date > BASE_END)]
    out = df.sort_values("date")[["date", "qty_sold"]].copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out.rename(columns={"date": "Tanggal", "qty_sold": "Terjual"})


def update_qty(product_id: str, tanggal, new_qty: int):
    """Koreksi jumlah terjual pada tanggal tertentu (aman, tak ubah urutan)."""
    tanggal = pd.Timestamp(tanggal).normalize()
    df = pd.read_csv(_CSV_PATH, parse_dates=["date"])
    mask = (df.product_id == product_id) & (df.date == tanggal)
    if not mask.any():
        return False, f"Tidak ada catatan {product_id} pada {tanggal.date()}."
    df.loc[mask, "qty_sold"] = int(new_qty)
    df.to_csv(_CSV_PATH, index=False)
    _reset_cache()
    return True, f"✓ Jumlah {tanggal.date()} diperbarui jadi {new_qty}."


def delete_last(product_id: str):
    """
    Hapus catatan TERAKHIR (paling baru) agar urutan tetap rapat tanpa gap.
    Hanya boleh menghapus catatan manual (setelah data dasar).
    """
    df = pd.read_csv(_CSV_PATH, parse_dates=["date"])
    sub = df[(df.product_id == product_id) & (df.date > BASE_END)]
    if sub.empty:
        return False, "Tidak ada catatan manual yang bisa dihapus (hanya data dasar)."
    last_date = sub["date"].max()
    df = df[~((df.product_id == product_id) & (df.date == last_date))]
    df.to_csv(_CSV_PATH, index=False)
    _reset_cache()
    return True, f"✓ Catatan {last_date.date()} dihapus."


def _reset_cache():
    try:
        import core.forecasting as fc
        fc._HIST = None
    except Exception:
        pass
