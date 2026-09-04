"""
config.py - Parameter domain (sumber acuan tunggal).

Isi: identitas studi kasus, produk & base demand (Sec. 3.2.2), bahan baku +
parameter EOQ/ROP (Sec. 3.6.4), Bill of Materials (Sec. 3.6.3), parameter
simulasi data sintetis, dan palet warna dashboard.

Nilai di sini adalah default prototipe. Saat sistem berjalan, produk, bahan
baku, stok, dan BOM dibaca dari database (data/store.py) yang dapat diubah
sendiri oleh pemilik UMKM lewat halaman Manajemen.
"""

# IDENTITAS STUDI KASUS
STUDI_KASUS = {
    "nama": "UMKM Olahan Stroberi — Desa Wisata Alamendah",
    "lokasi": "Ciwidey, Kabupaten Bandung, Jawa Barat",
    "koordinat": (-7.1167, 107.3833),  # Ciwidey, dipakai untuk fetch Open-Meteo
    "horizon_hari": 7,                  # short-term forecasting (Sec. batasan masalah)
}

# PRODUK (target forecasting) — base demand mengacu Sec. 3.2.2
# mu = rata-rata permintaan harian; weekend & holiday multiplier dari kalibrasi domain.
PRODUK = {
    "P001": {
        "nama": "Selai Stroberi",
        "satuan": "jar",
        "mu": 40,              # ~40 unit/hari (Sec. 3.2.2)
        "harga": 15_000,       # Rp (contoh dataset Tabel 3.x)
        "noise_pct": 0.10,     # sigma noise = 10% mu
    },
    "P002": {
        "nama": "Strawberry Cake",
        "satuan": "loyang",
        "mu": 15,              # ~15 unit/hari
        "harga": 22_000,
        "noise_pct": 0.10,
    },
    "P003": {
        "nama": "Jus Stroberi Segar",
        "satuan": "cup",
        "mu": 80,              # ~80 unit/hari
        "harga": 12_000,
        "noise_pct": 0.10,
    },
}

# BAHAN BAKU (raw materials) + parameter inventori — Sec. 3.6.4
# stok        : level stok saat ini (satuan masing-masing)
# lead_time   : L, hari (Sec. 3.6.4, masuk ke ROP)
# S           : ordering cost / biaya pesan per order (Rp)
# H           : holding cost / biaya simpan per satuan per HARI (Rp)
# pemasok     : referensi ke dict PEMASOK
BAHAN_BAKU = {
    "M01": {"nama": "Stroberi Segar", "satuan": "kg",    "stok": 42,  "lead_time": 1, "S": 25_000, "H": 120, "pemasok": "S1"},
    "M02": {"nama": "Gula Pasir",     "satuan": "kg",    "stok": 120, "lead_time": 2, "S": 15_000, "H": 30,  "pemasok": "S2"},
    "M03": {"nama": "Tepung Terigu",  "satuan": "kg",    "stok": 85,  "lead_time": 2, "S": 15_000, "H": 25,  "pemasok": "S2"},
    "M04": {"nama": "Mentega",        "satuan": "kg",    "stok": 30,  "lead_time": 2, "S": 20_000, "H": 90,  "pemasok": "S3"},
    "M05": {"nama": "Susu Segar",     "satuan": "liter", "stok": 60,  "lead_time": 2, "S": 18_000, "H": 70,  "pemasok": "S3"},
    "M06": {"nama": "Telur Ayam",     "satuan": "butir", "stok": 500, "lead_time": 1, "S": 12_000, "H": 8,   "pemasok": "S4"},
}

# BILL OF MATERIALS — Sec. 3.6.3
# BOM[produk][bahan] = kebutuhan bahan baku per 1 unit produk jadi
BOM = {
    "P001": {"M01": 0.30, "M02": 0.20},                                              # Selai: stroberi + gula
    "P002": {"M03": 0.25, "M02": 0.15, "M04": 0.12, "M06": 3.0, "M05": 0.10, "M01": 0.08},  # Cake
    "P003": {"M01": 0.15, "M02": 0.03, "M05": 0.10},                                 # Jus
}

# PEMASOK (stakeholder hulu / inbound supply chain) — Sec. 3.6.4 (lead time)
PEMASOK = {
    "S1": {"nama": "Kebun Stroberi Alamendah",   "wilayah": "Ciwidey",  "lead_time": 1, "status": "Aktif"},
    "S2": {"nama": "Distributor Sembako Ciwidey", "wilayah": "Ciwidey",  "lead_time": 2, "status": "Aktif"},
    "S3": {"nama": "Pemasok Dairy Lembang",       "wilayah": "Lembang",  "lead_time": 2, "status": "Aktif"},
    "S4": {"nama": "Peternakan Ayam Pasirjambu",  "wilayah": "Pasirjambu","lead_time": 1, "status": "Aktif"},
}

# PARAMETER INVENTORI GLOBAL — Sec. 3.6.4
SERVICE_LEVEL = 0.95
Z_SCORE = 1.65          # z untuk service level 95% (Sec. 3.6.4)

# PARAMETER SIMULASI DATA SINTETIS — Sec. 3.2.2
SIM = {
    "tanggal_awal": "2023-01-01",
    "tanggal_akhir": "2025-12-31",          # 1.096 observasi/produk (3 tahun)
    "weekend_mult": (1.8, 2.5),             # Sabtu-Minggu 1.8-2.5x hari kerja
    "holiday_mult": (2.5, 4.0),             # holiday spike 2.5-4x
    "holiday_window": (-1, 2),              # H-1 s/d H+2
    "rain_threshold_mm": 20.0,              # > 20mm -> hari "tidak nyaman"
    "rain_penalty": (-0.40, -0.20),         # penalti -20% s/d -40%
    "seed": 42,
}

# MODEL KANDIDAT — sesuai BAB I & III (BUKAN LSTM/ANN)
# 'mape_ref' = ekspektasi MAPE prototipe, dikalibrasi dari literatur:
#   Hybrid Prophet-XGBoost hipotesis terbaik (Liu & Wen 2026: MAPE ~8.6%),
#   XGBoost kuat (~10.3%), Prophet & ARIMA sebagai baseline.
MODEL = {
    "ARIMA":   {"label": "ARIMA",                  "warna": "#9AA5B1", "mape_ref": 0.327, "rank": 4},
    "Prophet": {"label": "Prophet",                "warna": "#5B8DEF", "mape_ref": 0.083, "rank": 3},
    "Hybrid":  {"label": "Hybrid Prophet–XGBoost", "warna": "#0E8A6B", "mape_ref": 0.078, "rank": 2},
    "XGBoost": {"label": "XGBoost",                "warna": "#2EA37A", "mape_ref": 0.0763, "rank": 1},
}
MODEL_TERBAIK = "XGBoost"

# PALET WARNA (tema akademik clean — hijau/biru supply chain)
WARNA = {
    "primer":    "#0E8A6B",   # hijau teal (supply chain)
    "sekunder":  "#16344A",   # deep blue (logistik) — digelapkan utk kontras
    "aksen":     "#2EA37A",
    "kritis":    "#C42B3C",
    "waspada":   "#B5731A",
    "aman":      "#1E8E64",
    "bg":        "#F4F6F8",   # area kerja (abu sangat muda)
    "kartu":     "#FFFFFF",   # kartu putih -> kontras dgn bg
    "garis":     "#DCE2E7",
    "teks":      "#16202B",   # near-black
    "teks_lemah":"#54616E",   # digelapkan agar terbaca
}
