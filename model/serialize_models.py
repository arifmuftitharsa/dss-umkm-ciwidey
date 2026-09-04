"""
serialize_models.py - Latih & simpan model terpilih (XGBoost) ke .joblib.

Melatih XGBoost pada data train+val tiap produk, lalu menyimpan model beserta
meta (daftar kolom fitur + hyperparameter) ke ./models_trained/.

PENTING: setelah menjalankan ini, salin isi ./models_trained/ ke
dss-umkm/models_trained/ agar web app memakai model yang sama.
"""
import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import config
import feature_engineering as fe
from models import model_xgboost as mx

OUT = Path(__file__).resolve().parent / "models_trained"
OUT.mkdir(exist_ok=True)


def main():
    df_all = pd.read_csv(config.DATA_PATH)
    feats = fe.get_feature_columns("full")
    meta = {"feature_cols": feats, "products": {}}

    for pid in config.PRODUCTS:
        print(f"> Melatih XGBoost final untuk {pid} ...", flush=True)
        df = fe.load_product_series(df_all, pid)
        df = fe.build_features(df)
        train, val, test = fe.temporal_split(df)

        # Normalisasi StandardScaler (Sec. 3.3.4): fit HANYA di train,
        # val/test hanya di-transform.
        Xtr_raw = train[feats].fillna(0)
        Xvl_raw = val[feats].fillna(0)
        scaler = StandardScaler().fit(Xtr_raw)
        Xtr = scaler.transform(Xtr_raw)
        Xvl = scaler.transform(Xvl_raw)

        # tuning Optuna, lalu fit model final (val = eval_set early stopping)
        best = mx.tune_xgboost(Xtr, train["qty_sold"].values,
                               Xvl, val["qty_sold"].values,
                               n_trials=config.N_OPTUNA_TRIALS,
                               seed=config.RANDOM_SEED)
        model = mx.train_xgboost(Xtr, train["qty_sold"].values,
                                 Xvl, val["qty_sold"].values, best,
                                 config.RANDOM_SEED)

        # Scaler + model dibungkus jadi satu Pipeline agar ikut tersimpan di
        # .joblib. Saat inference, pipeline.predict() menerima fitur MENTAH dan
        # men-scale-nya otomatis dengan scaler yang sama seperti saat pelatihan.
        pipe = Pipeline([("scaler", scaler), ("model", model)])
        joblib.dump(pipe, OUT / f"xgb_{pid}.joblib")
        meta["products"][pid] = {"best_params": best}
        print(f"  OK: tersimpan: xgb_{pid}.joblib")

    with open(OUT / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\nOK: Semua model & meta tersimpan di {OUT}")


if __name__ == "__main__":
    main()
