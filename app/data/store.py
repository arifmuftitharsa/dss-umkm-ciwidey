"""
data/store.py - Persistensi konfigurasi UMKM ke SQLite.

Menyimpan data master yang dapat diubah pemilik agar tidak hilang saat aplikasi
di-restart.

Tabel:
  produk      : id, nama, satuan, mu, harga
  bahan_baku  : id, nama, satuan, stok, lead_time, ordering_cost, holding_cost
  bom         : produk_id, bahan_id, qty (kebutuhan bahan per 1 unit produk)

Saat deployment (Sec. 3.7.1), SQLite dapat diganti PostgreSQL tanpa mengubah
logika aplikasi karena skema tabelnya sama.
"""
from __future__ import annotations
import logging
import sqlite3
from pathlib import Path
import pandas as pd

from config import PRODUK, BAHAN_BAKU, BOM

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "dss_umkm.db"


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db(reset: bool = False):
    """Buat tabel & isi awal (seed) dari config bila database masih kosong."""
    if reset and DB_PATH.exists():
        DB_PATH.unlink()

    con = _conn()
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS produk (
            id TEXT PRIMARY KEY, nama TEXT, satuan TEXT,
            mu REAL, harga REAL
        );
        CREATE TABLE IF NOT EXISTS bahan_baku (
            id TEXT PRIMARY KEY, nama TEXT, satuan TEXT,
            stok REAL, lead_time INTEGER,
            ordering_cost REAL, holding_cost REAL
        );
        CREATE TABLE IF NOT EXISTS bom (
            produk_id TEXT, bahan_id TEXT, qty REAL,
            PRIMARY KEY (produk_id, bahan_id)
        );
        CREATE TABLE IF NOT EXISTS libur_window (
            jenis TEXT PRIMARY KEY, h_minus INTEGER, h_plus INTEGER
        );
        CREATE TABLE IF NOT EXISTS pengaturan_sistem (
            kunci TEXT PRIMARY KEY, nilai TEXT
        );
    """)
    con.commit()

    # seed hanya bila tabel produk kosong
    if cur.execute("SELECT COUNT(*) FROM produk").fetchone()[0] == 0:
        for pid, p in PRODUK.items():
            cur.execute("INSERT INTO produk VALUES (?,?,?,?,?)",
                        (pid, p["nama"], p["satuan"], p["mu"], p["harga"]))
        for mid, m in BAHAN_BAKU.items():
            cur.execute("INSERT INTO bahan_baku VALUES (?,?,?,?,?,?,?)",
                        (mid, m["nama"], m["satuan"], m["stok"],
                         m["lead_time"], m["S"], m["H"]))
        for pid, row in BOM.items():
            for mid, qty in row.items():
                cur.execute("INSERT INTO bom VALUES (?,?,?)", (pid, mid, qty))
        con.commit()

    # seed window libur — SEMUA nama libur (selalu dilengkapi, upgrade DB lama)
    # INSERT OR IGNORE: baris baru ditambah, yang sudah ada (mis. editan user) tetap
    seed = [("(default)", 1, 2)]
    khusus = {"idul fitri": (2, 7), "natal": (2, 3), "tahun baru masehi": (1, 2)}
    canonical = {"(default)"}
    try:
        import holidays as _hol
        from data import weather as _w   # untuk normalisasi nama ke Indonesia

        nama_set = set()
        for thn in [2023, 2024, 2025, 2026, 2027]:
            try:
                hol = _hol.Indonesia(years=thn, language="id")
            except Exception:
                hol = _hol.Indonesia(years=thn)
            for _, nama in hol.items():
                nama_set.add(_w.normalize_holiday_name(nama))
        for nama in sorted(nama_set):
            low = nama.lower()
            hm, hp = 1, 2
            for k, (a, b2) in khusus.items():
                if k in low:
                    hm, hp = a, b2
                    break
            seed.append((nama, hm, hp))
            canonical.add(nama)
    except Exception:
        for nm, w in [("Hari Raya Idul Fitri", (2, 7)), ("Hari Raya Natal", (2, 3)),
                      ("Tahun Baru Masehi", (1, 2))]:
            seed.append((nm, w[0], w[1])); canonical.add(nm)

    # HAPUS semua baris yang bukan nama kanonik Indonesia (mis. sisa Inggris/estimated)
    existing = [r[0] for r in cur.execute("SELECT jenis FROM libur_window").fetchall()]
    buang = [j for j in existing if j not in canonical]
    if buang:
        cur.executemany("DELETE FROM libur_window WHERE jenis=?", [(j,) for j in buang])
    cur.executemany("INSERT OR IGNORE INTO libur_window VALUES (?,?,?)", seed)
    con.commit()
    con.close()


# --- Pembacaan
def get_produk() -> pd.DataFrame:
    con = _conn(); df = pd.read_sql("SELECT * FROM produk", con); con.close()
    return df


def get_bahan() -> pd.DataFrame:
    con = _conn(); df = pd.read_sql("SELECT * FROM bahan_baku", con); con.close()
    return df


def get_bom() -> pd.DataFrame:
    con = _conn(); df = pd.read_sql("SELECT * FROM bom", con); con.close()
    return df


def get_bom_matrix() -> pd.DataFrame:
    """BOM sebagai matriks produk × bahan (untuk st.data_editor yang ramah)."""
    bom, prod, bahan = get_bom(), get_produk(), get_bahan()
    mat = pd.DataFrame(0.0, index=prod["id"], columns=bahan["id"])
    for _, r in bom.iterrows():
        if r.produk_id in mat.index and r.bahan_id in mat.columns:
            mat.loc[r.produk_id, r.bahan_id] = r.qty
    return mat


# --- Adapter: kembalikan dict berformat config (dipakai core/inventory.py)
def get_bahan_dict() -> dict:
    """{mid: {nama, satuan, stok, lead_time, S, H, pemasok}} — seperti config.BAHAN_BAKU."""
    from config import BAHAN_BAKU as _CFG  # ambil 'pemasok' (tak diedit di manajemen)
    out = {}
    for _, r in get_bahan().iterrows():
        out[r.id] = {
            "nama": r.nama, "satuan": r.satuan, "stok": r.stok,
            "lead_time": int(r.lead_time), "S": r.ordering_cost, "H": r.holding_cost,
            "pemasok": _CFG.get(r.id, {}).get("pemasok", "S1"),
        }
    return out


def get_bom_dict() -> dict:
    """{pid: {mid: qty}} — seperti config.BOM."""
    out = {}
    for _, r in get_bom().iterrows():
        out.setdefault(r.produk_id, {})[r.bahan_id] = r.qty
    return out


def get_produk_dict() -> dict:
    """{pid: {nama, satuan, mu, harga}} — sumber kebenaran tunggal untuk
    daftar produk (T-4), dipakai core/forecasting.py, core/inventory.py,
    views/forecasting.py, views/overview.py.

    init_db() dipanggil dulu -- idempotent dan self-healing: kalau tabel
    produk belum ada / masih kosong, ia dibuat & di-seed otomatis dari
    config.PRODUK (lihat init_db()), sehingga "DB kosong" BUKAN kondisi
    yang butuh fallback di sini. Dict kosong hasil query yang SUKSES tetap
    dikembalikan apa adanya (misal pemilik sengaja menghapus semua produk
    lewat dashboard) -- bukan alasan fallback, supaya tak diam-diam
    memunculkan kembali produk default yang sudah sengaja dihapus.

    Fallback ke config.PRODUK statis HANYA dipakai kalau ada kegagalan
    sungguhan (file database korup, permission error, dsb) -- dicatat lewat
    logger.warning karena itu sinyal masalah infrastruktur yang perlu
    diperiksa developer, bukan sesuatu yang bisa dilakukan pemilik UMKM
    dari UI (beda pertimbangan dari indikator used_climatology T-7b)."""
    try:
        init_db()
        out = {}
        for _, r in get_produk().iterrows():
            out[r.id] = {"nama": r.nama, "satuan": r.satuan,
                         "mu": r.mu, "harga": r.harga}
        return out
    except Exception as e:
        logger.warning(
            "get_produk_dict: gagal baca tabel produk dari database (%s: %s) "
            "-- pakai config.PRODUK statis sebagai cadangan darurat. Ini "
            "sinyal masalah infrastruktur (database korup/permission), "
            "bukan kondisi normal -- periksa data/dss_umkm.db.",
            type(e).__name__, e,
        )
        return PRODUK


# --- Window libur (editable)
def get_window_df() -> pd.DataFrame:
    con = _conn(); df = pd.read_sql("SELECT * FROM libur_window", con); con.close()
    return df


def get_window_config() -> dict:
    """{jenis: (h_minus, h_plus)} dibaca weather.py untuk menentukan window."""
    out = {}
    for _, r in get_window_df().iterrows():
        out[r.jenis.lower()] = (int(r.h_minus), int(r.h_plus))
    return out


def save_window_df(df: pd.DataFrame):
    con = _conn()
    df.to_sql("libur_window", con, if_exists="replace", index=False)
    con.close()


# --- Titik reset operasional (T-1): batas antara data training sintetis
# dan catatan penjualan asli. None = belum diaktifkan; form Catat Penjualan
# terkunci sampai pemilik menekan "Mulai Pakai Data Real Hari Ini".
def get_tanggal_mulai_operasional() -> pd.Timestamp | None:
    con = _conn()
    row = con.execute(
        "SELECT nilai FROM pengaturan_sistem WHERE kunci = 'tanggal_mulai_operasional'"
    ).fetchone()
    con.close()
    return None if row is None else pd.Timestamp(row[0])


def set_tanggal_mulai_operasional(tanggal) -> None:
    """Aktifkan titik reset. Aksi eksplisit sekali jalan (bukan otomatis) --
    dipicu tombol konfirmasi di views/pengaturan.py."""
    tanggal = pd.Timestamp(tanggal).normalize()
    con = _conn()
    con.execute(
        "INSERT OR REPLACE INTO pengaturan_sistem VALUES ('tanggal_mulai_operasional', ?)",
        (tanggal.strftime("%Y-%m-%d"),),
    )
    con.commit()
    con.close()


def reset_tanggal_mulai_operasional() -> None:
    """Kembalikan ke kondisi belum diaktifkan (form terkunci lagi).

    KHUSUS DEVELOPMENT/TESTING -- tak ada tombol UI untuk ini di produksi
    (sengaja, demi keamanan demo Ciwidey). Panggil manual lewat terminal
    saat perlu mengulang pengujian T-1 dari kondisi awal:

        cd app && venv/Scripts/python.exe -c \
            "import sys; sys.path.insert(0,'.'); from data import store; \
             store.reset_tanggal_mulai_operasional()"
    """
    con = _conn()
    con.execute(
        "DELETE FROM pengaturan_sistem WHERE kunci = 'tanggal_mulai_operasional'"
    )
    con.commit()
    con.close()


# --- Penyimpanan (dipanggil dari halaman pengaturan)
def save_produk(df: pd.DataFrame):
    con = _conn()
    df.to_sql("produk", con, if_exists="replace", index=False)
    con.close()


def save_bahan(df: pd.DataFrame):
    con = _conn()
    df.to_sql("bahan_baku", con, if_exists="replace", index=False)
    con.close()


def save_bom_matrix(mat: pd.DataFrame):
    """Simpan matriks BOM kembali ke bentuk panjang (long)."""
    rows = []
    for pid in mat.index:
        for mid in mat.columns:
            qty = float(mat.loc[pid, mid])
            if qty > 0:
                rows.append((pid, mid, qty))
    con = _conn(); cur = con.cursor()
    cur.execute("DELETE FROM bom")
    cur.executemany("INSERT INTO bom VALUES (?,?,?)", rows)
    con.commit(); con.close()


if __name__ == "__main__":
    init_db(reset=True)
    print("DB dibuat & di-seed.")
    print("\nProduk:\n", get_produk())
    print("\nBahan baku:\n", get_bahan())
    print("\nBOM matrix:\n", get_bom_matrix())
