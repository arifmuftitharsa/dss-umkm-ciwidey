"""
run_pipeline.py - Orchestrator pipeline pemodelan. JALANKAN FILE INI.

Alur (Bab III) -> hasil (Bab IV):
  1. feature engineering + split          (Sec. 3.3)
  2. latih & evaluasi ARIMA, Prophet,
     XGBoost, Hybrid Prophet-XGBoost      (Sec. 3.4)
  3. metrik MAE/RMSE/MAPE pada H+1 & H+7  (Sec. 3.6.1)
  4. ablation study variabel eksogen      (Sec. 3.6.2)
  5. BOM + EOQ/ROP + simulasi A vs B      (Sec. 3.6.3-3.6.5)

Output CSV/JSON ke ./outputs/.
"""

import json
import warnings
import numpy as np
import pandas as pd

import config
import feature_engineering as fe
import evaluate as ev
from models import model_arima as m_arima
from models import model_prophet as m_prophet
from models import model_xgboost as m_xgb
from models import model_hybrid as m_hybrid

warnings.filterwarnings("ignore")
np.random.seed(config.RANDOM_SEED)

YEARS = [2023, 2024, 2025]
HOLIDAYS_DF = m_prophet._make_id_holidays(YEARS)


def run_models_for_product(pid, df_all, verbose=True):
    """Latih & evaluasi keempat model untuk satu produk. Return list of dict."""
    df = fe.load_product_series(df_all, pid)
    df = fe.build_features(df)
    train, val, test = fe.temporal_split(df)

    # gabung train+val untuk fit final (test sekali pakai)
    trainval = pd.concat([train, val]).reset_index(drop=True)

    results = []
    feat_full = fe.get_feature_columns("full")

    for horizon in config.HORIZONS:
        # ===== ARIMA (univariat, baseline statistik) =====
        if verbose:
            print(f"  [{pid}] ARIMA  H+{horizon} ...", flush=True)
        y_true, y_pred, order = m_arima.fit_predict_arima(
            trainval["qty_sold"], test["qty_sold"], horizon=horizon)
        results.append({"product": pid, "model": "ARIMA", "horizon": f"H+{horizon}",
                        **ev.all_metrics(y_true, y_pred)})

    # ===== Prophet (multi-horizon via prediksi penuh test) =====
    if verbose:
        print(f"  [{pid}] Prophet ...", flush=True)
    p_trainval = m_prophet.build_prophet_df(trainval, use_weather=True)
    prophet_params = {"changepoint_prior_scale": 0.05, "seasonality_prior_scale": 10.0}
    prophet = m_prophet.fit_prophet(p_trainval, prophet_params, use_weather=True,
                                    holidays_df=HOLIDAYS_DF)
    p_test = m_prophet.build_prophet_df(test, use_weather=True)
    yhat_prophet = m_prophet.predict_prophet(prophet, p_test)
    for horizon in config.HORIZONS:
        # untuk Prophet, H+1 vs H+7 dibedakan via offset evaluasi
        yt = test["qty_sold"].values[horizon - 1:]
        yp = yhat_prophet[horizon - 1:]
        results.append({"product": pid, "model": "Prophet", "horizon": f"H+{horizon}",
                        **ev.all_metrics(yt, yp)})

    # ===== XGBoost (tuning Optuna) =====
    if verbose:
        print(f"  [{pid}] XGBoost (tuning Optuna) ...", flush=True)
    # Normalisasi StandardScaler (Sec. 3.3.4), khusus fitur XGBoost.
    # fillna(0) DULU baru scaling, agar baris awal tanpa lag/rolling
    # diperlakukan sama di train, val, dan test.
    trs, vals, tes, _ = fe.scale_features(train.fillna(0), val.fillna(0),
                                          test.fillna(0), feat_full)
    Xtr = trs[feat_full].values
    ytr = trs["qty_sold"].values
    Xvl = vals[feat_full].values
    yvl = vals["qty_sold"].values
    best_params = m_xgb.tune_xgboost(Xtr, ytr, Xvl, yvl,
                                     n_trials=config.N_OPTUNA_TRIALS,
                                     seed=config.RANDOM_SEED)
    # Model final dilatih di train; val dipakai sebagai eval_set early stopping
    # sehingga tidak boleh sekaligus jadi data latih.
    Xte = tes[feat_full].values
    yte = tes["qty_sold"].values
    xgb_final = m_xgb.train_xgboost(Xtr, ytr, Xvl, yvl, best_params, config.RANDOM_SEED)
    yhat_xgb = m_xgb.predict_xgboost(xgb_final, Xte)
    for horizon in config.HORIZONS:
        yt = yte[horizon - 1:]
        yp = yhat_xgb[horizon - 1:]
        results.append({"product": pid, "model": "XGBoost", "horizon": f"H+{horizon}",
                        **ev.all_metrics(yt, yp)})

    # ===== Hybrid Prophet–XGBoost =====
    if verbose:
        print(f"  [{pid}] Hybrid Prophet–XGBoost ...", flush=True)
    hybrid = m_hybrid.fit_hybrid(train, val, prophet_params, HOLIDAYS_DF,
                                 seed=config.RANDOM_SEED)
    yhat_hybrid = m_hybrid.predict_hybrid(hybrid, test)
    for horizon in config.HORIZONS:
        yt = yte[horizon - 1:]
        yp = yhat_hybrid[horizon - 1:]
        results.append({"product": pid, "model": "Hybrid", "horizon": f"H+{horizon}",
                        **ev.all_metrics(yt, yp)})

    return results, {"xgb_best_params": best_params, "arima_order": order}


def run_ablation(pid, df_all, verbose=True):
    """Ablation study skenario A-E pada XGBoost (Sec. 3.6.2), horizon H+1.

    Baseline (A) benar-benar hanya lag+rolling; fitur ditambahkan bertahap:
    day-of-week -> weekend -> holiday -> rainfall, agar kontribusi tiap
    kelompok fitur terisolasi dengan benar.
    """
    df = fe.load_product_series(df_all, pid)
    df = fe.build_features(df)
    train, val, test = fe.temporal_split(df)
    yte = test["qty_sold"].values

    rows = []
    scenarios = {
        "A (lag+rolling)": "A",
        "B (+day_of_week)": "B",
        "C (+weekend)": "C",
        "D (+holiday)": "D",
        "E (+rainfall / full)": "E",
    }
    for label, sc in scenarios.items():
        feats = fe.get_feature_columns(sc)
        # Normalisasi per skenario (Sec. 3.3.4), scaler di-fit hanya di train
        trs, vals, tes, _ = fe.scale_features(train.fillna(0), val.fillna(0),
                                              test.fillna(0), feats)
        model = m_xgb.train_xgboost(trs[feats].values, trs["qty_sold"].values,
                                    vals[feats].values, vals["qty_sold"].values,
                                    seed=config.RANDOM_SEED)
        yhat = m_xgb.predict_xgboost(model, tes[feats].values)
        rows.append({"product": pid, "scenario": label, **ev.all_metrics(yte, yhat)})
    return rows


def run_inventory(df_all, best_model_forecasts, verbose=True):
    """
    Simulasi inventori (3.6.5).
    best_model_forecasts : dict {pid: array forecast test} dari model terbaik.
    Permintaan aktual (proksi) = qty_sold test set.
    """
    import inventory as inv

    # kebutuhan bahan baku aktual (dari qty test) & forecast
    actual_products, forecast_products = {}, {}
    for pid in config.PRODUCTS:
        df = fe.load_product_series(df_all, pid)
        _, _, test = fe.temporal_split(fe.build_features(df))
        actual_products[pid] = test["qty_sold"].values
        forecast_products[pid] = best_model_forecasts[pid]

    actual_mats = inv.forecast_to_materials(actual_products)
    forecast_mats = inv.forecast_to_materials(forecast_products)

    recs, sim_rows = [], []
    for mat in config.BOM:
        rec = inv.inventory_recommendation(forecast_mats[mat], mat)
        recs.append({"material_id": mat, **rec})

        res_a = inv.simulate_inventory(actual_mats[mat], "A", mat_id=mat)
        res_b = inv.simulate_inventory(actual_mats[mat], "B",
                                       forecast_demand=forecast_mats[mat], mat_id=mat)
        sim_rows.append({
            "material": config.MATERIALS[mat],
            "A_stockout_%": res_a["stockout_rate"],
            "A_inv_days": res_a["avg_inventory_days"],
            "B_stockout_%": res_b["stockout_rate"],
            "B_inv_days": res_b["avg_inventory_days"],
        })
    return recs, sim_rows


def main():
    print("=" * 70)
    print("PIPELINE PEMODELAN DSS UMKM — menjalankan BAB III → hasil BAB IV")
    print("=" * 70)
    df_all = pd.read_csv(config.DATA_PATH)

    # 1) Evaluasi komparatif 4 model
    all_results, meta = [], {}
    best_forecasts = {}
    for pid in config.PRODUCTS:
        print(f"\n> Produk {pid} ({config.PRODUCT_NAMES[pid]})")
        res, m = run_models_for_product(pid, df_all)
        all_results.extend(res)
        meta[pid] = m

        # simpan forecast model terbaik (hybrid) untuk modul inventori
        df = fe.load_product_series(df_all, pid)
        _, _, test = fe.temporal_split(fe.build_features(df))
        train, val, _ = fe.temporal_split(fe.build_features(
            fe.load_product_series(df_all, pid)))
        prophet_params = {"changepoint_prior_scale": 0.05, "seasonality_prior_scale": 10.0}
        hybrid = m_hybrid.fit_hybrid(train, val, prophet_params, HOLIDAYS_DF,
                                     seed=config.RANDOM_SEED)
        best_forecasts[pid] = m_hybrid.predict_hybrid(hybrid, test)

    df_results = pd.DataFrame(all_results)
    df_results.to_csv(config.OUTPUT_DIR / "hasil_komparatif_model.csv", index=False)

    # 2) Ablation study
    print("\n> Ablation study variabel eksogen (skenario A–D)")
    ablation_rows = []
    for pid in config.PRODUCTS:
        ablation_rows.extend(run_ablation(pid, df_all))
    df_ablation = pd.DataFrame(ablation_rows)
    df_ablation.to_csv(config.OUTPUT_DIR / "hasil_ablation_study.csv", index=False)

    # 3) Inventori
    print("\n> Modul inventori: konversi BOM + EOQ/ROP + simulasi A vs B")
    recs, sim_rows = run_inventory(df_all, best_forecasts)
    pd.DataFrame(recs).to_csv(config.OUTPUT_DIR / "rekomendasi_inventori.csv", index=False)
    pd.DataFrame(sim_rows).to_csv(config.OUTPUT_DIR / "simulasi_inventori.csv", index=False)

    with open(config.OUTPUT_DIR / "meta_model.json", "w") as f:
        json.dump(meta, f, indent=2, default=str)

    # --- Ringkasan ke layar
    print("\n" + "=" * 70)
    print("HASIL KOMPARATIF MODEL (MAE / RMSE / MAPE)")
    print("=" * 70)
    print(df_results.to_string(index=False))

    print("\n" + "=" * 70)
    print("ABLATION STUDY (XGBoost, H+1)")
    print("=" * 70)
    print(df_ablation.to_string(index=False))

    print("\n" + "=" * 70)
    print("SIMULASI INVENTORI — Skenario A (manual) vs B (DSS)")
    print("=" * 70)
    print(pd.DataFrame(sim_rows).to_string(index=False))

    print("\nOK: Semua output tersimpan di ./outputs/")


if __name__ == "__main__":
    main()
