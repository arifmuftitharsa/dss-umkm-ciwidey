"""
evaluate.py - Metrik evaluasi peramalan (Sec. 3.6.1).

MAE, RMSE, dan MAPE sesuai Hyndman & Koehler (2006).
"""

import numpy as np


def mae(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true, y_pred, eps=1e-8):
    """MAPE (%) — abaikan titik dengan y_true ~ 0 agar stabil (3.6.1)."""
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    mask = np.abs(y_true) > eps
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def all_metrics(y_true, y_pred):
    return {
        "MAE": round(mae(y_true, y_pred), 3),
        "RMSE": round(rmse(y_true, y_pred), 3),
        "MAPE": round(mape(y_true, y_pred), 3),
    }
