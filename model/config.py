"""
config.py - Parameter terpusat pipeline pemodelan.

Semua angka mengacu ke Bab III-IV laporan (produk, BOM, split, horizon,
parameter inventori, ruang fitur, tuning).
"""

from pathlib import Path

# --- Path
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data_sintetis_permintaan.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# --- Produk (Tabel 4.3)
PRODUCTS = ["P001", "P002", "P003"]
PRODUCT_NAMES = {
    "P001": "Selai Stroberi (250g)",
    "P002": "Strawberry Cake (loyang)",
    "P003": "Jus Stroberi Segar (cup)",
}

# --- Bahan baku (Tabel 4.4)
MATERIALS = {
    "BB01": "Stroberi Segar",
    "BB02": "Gula Pasir",
    "BB03": "Tepung Terigu",
    "BB04": "Mentega",
    "BB05": "Susu Segar",
    "BB06": "Telur Ayam",
}

# --- Bill of Materials (Tabel 4.5): kebutuhan bahan baku per 1 unit produk
# Satuan: BB01-BB05 kg/liter, BB06 butir.
BOM = {
    # material: {produk: qty per unit produk}
    "BB01": {"P001": 0.300, "P002": 0.200, "P003": 0.150},   # Stroberi (kg)
    "BB02": {"P001": 0.150, "P002": 0.100, "P003": 0.030},   # Gula (kg)
    "BB03": {"P001": 0.0,   "P002": 0.200, "P003": 0.0},     # Tepung (kg)
    "BB04": {"P001": 0.0,   "P002": 0.100, "P003": 0.0},     # Mentega (kg)
    "BB05": {"P001": 0.0,   "P002": 0.150, "P003": 0.050},   # Susu (liter)
    "BB06": {"P001": 0.0,   "P002": 2,     "P003": 0.0},     # Telur (butir)
}

# --- Pembagian temporal 70/15/15 tanpa shuffling (Sec. 3.3.5)
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# --- Horizon evaluasi (Sec. 3.6.1)
HORIZONS = [1, 7]   # H+1 (besok) dan H+7 (7 hari ke depan)

# --- Parameter inventori (Sec. 3.6.4)
SERVICE_LEVEL_Z = 1.65        # Z-score untuk service level 95%
# Biaya per bahan baku (ilustratif; dikonfigurasi pemilik UMKM di dashboard).
# ordering_cost: Rp/order | holding_cost: Rp/satuan/hari | lead_time: hari
INVENTORY_PARAMS = {
    "BB01": {"ordering_cost": 25000, "holding_cost": 2000, "lead_time": 2},
    "BB02": {"ordering_cost": 15000, "holding_cost": 500,  "lead_time": 3},
    "BB03": {"ordering_cost": 15000, "holding_cost": 500,  "lead_time": 3},
    "BB04": {"ordering_cost": 20000, "holding_cost": 1500, "lead_time": 3},
    "BB05": {"ordering_cost": 20000, "holding_cost": 1800, "lead_time": 2},
    "BB06": {"ordering_cost": 10000, "holding_cost": 1000, "lead_time": 2},
}

# --- Fitur lag & rolling untuk XGBoost (Sec. 3.3.3)
LAG_FEATURES = [1, 7, 14]
ROLLING_WINDOWS = [7, 30]

# --- Tuning Optuna (Sec. 3.5)
N_OPTUNA_TRIALS = 25
N_CV_FOLDS = 5
CV_TEST_DAYS = 30

RANDOM_SEED = 42
