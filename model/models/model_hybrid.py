"""
models/model_hybrid.py - Model 4: Hybrid Prophet-XGBoost (Sec. 3.4.4).

Arsitektur decomposition-residual (Zhang 2003; Liu & Wen 2026):
  1. Prophet memodelkan trend + seasonality + holiday
  2. residual r_t = y_t - prediksi Prophet
  3. XGBoost memprediksi r_t dari fitur lag/rolling/eksogen + interaksi
  4. prediksi akhir = Prophet + koreksi residual XGBoost
"""

import numpy as np
import pandas as pd

from models.model_prophet import build_prophet_df, fit_prophet, predict_prophet
from models.model_xgboost import train_xgboost


def add_interaction_features(df):
    """Interaksi eksplisit untuk XGBoost residual (Tahap 3)."""
    df = df.copy()
    df["weather_x_weekend"] = df["rainfall_mm"] * df["is_weekend"]
    df["weather_x_holiday"] = df["rainfall_mm"] * df["is_holiday"]
    return df


RESIDUAL_FEATURES = [
    "lag_1", "lag_7", "lag_14",
    "roll_mean_7", "roll_mean_30", "roll_std_7",
    "rainfall_mm", "is_weekend", "is_holiday",
    "hw_hm1", "hw_h0", "hw_hp1", "hw_hp2",
    "weather_x_weekend", "weather_x_holiday",
]


def fit_hybrid(train_feat, val_feat, prophet_params, holidays_df, seed=42):
    """
    train_feat, val_feat : dataframe sudah lewat build_features (punya kolom lag/rolling).
    Mengembalikan dict berisi model prophet + xgb residual.
    """
    # Tahap 1 — Prophet
    p_train = build_prophet_df(train_feat, use_weather=True)
    prophet = fit_prophet(p_train, prophet_params, use_weather=True,
                          holidays_df=holidays_df)

    # Tahap 2 — residual di train
    yhat_p_train = predict_prophet(prophet, p_train)
    resid_train = train_feat["qty_sold"].values - yhat_p_train

    # Tahap 3 — XGBoost belajar residual
    tr = add_interaction_features(train_feat)
    vl = add_interaction_features(val_feat)

    p_val = build_prophet_df(val_feat, use_weather=True)
    yhat_p_val = predict_prophet(prophet, p_val)
    resid_val = val_feat["qty_sold"].values - yhat_p_val

    X_tr = tr[RESIDUAL_FEATURES].fillna(0).values
    X_vl = vl[RESIDUAL_FEATURES].fillna(0).values

    xgb_resid = train_xgboost(X_tr, resid_train, X_vl, resid_val, seed=seed)

    return {"prophet": prophet, "xgb_resid": xgb_resid}


def predict_hybrid(models, feat_df):
    """Tahap 4 — gabungkan prediksi Prophet + koreksi residual XGBoost."""
    p_df = build_prophet_df(feat_df, use_weather=True)
    yhat_p = predict_prophet(models["prophet"], p_df)

    fd = add_interaction_features(feat_df)
    X = fd[RESIDUAL_FEATURES].fillna(0).values
    rhat = models["xgb_resid"].predict(X)

    return np.clip(yhat_p + rhat, 0, None)
