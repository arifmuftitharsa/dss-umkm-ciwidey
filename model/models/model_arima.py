"""
models/model_arima.py - Model 1: ARIMA / ARIMAX (Sec. 3.4.1).

Box-Jenkins: uji ADF untuk ordo d, grid search (p,q) dengan kriteria AIC.
ARIMAX = ARIMA + variabel eksogen (weekend, holiday, rainfall).
"""

import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

warnings.filterwarnings("ignore")


def determine_d(series, max_d=2, alpha=0.05):
    """Tentukan ordo differencing d via uji ADF (Section 3.4.1)."""
    d = 0
    s = series.copy()
    while d < max_d:
        try:
            pval = adfuller(s.dropna())[1]
        except Exception:
            break
        if pval < alpha:
            break
        s = s.diff().dropna()
        d += 1
    return d


def grid_search_order(series, d, p_range=(0, 3), q_range=(0, 3)):
    """Grid search (p,q) di sekitar kandidat, pilih AIC terendah."""
    best_aic, best_order = np.inf, (1, d, 1)
    for p in range(p_range[0], p_range[1] + 1):
        for q in range(q_range[0], q_range[1] + 1):
            if p == 0 and q == 0:
                continue
            try:
                m = ARIMA(series, order=(p, d, q)).fit()
                if m.aic < best_aic:
                    best_aic, best_order = m.aic, (p, d, q)
            except Exception:
                continue
    return best_order, best_aic


def fit_predict_arima(train_series, test_series, exog_train=None, exog_test=None,
                      horizon=1):
    """
    Latih ARIMA(X) pada train, prediksi test secara rolling-origin.
    horizon=1 : prediksi 1 langkah (H+1) dengan refit ringan (append).
    horizon=7 : prediksi 7 langkah ke depan dari tiap origin, ambil langkah ke-7.
    Mengembalikan (y_true_aligned, y_pred_aligned).
    """
    d = determine_d(train_series)
    order, _ = grid_search_order(train_series, d)

    history = list(train_series.values)
    exog_hist = list(exog_train.values) if exog_train is not None else None

    preds, trues = [], []
    test_vals = test_series.values
    exog_test_vals = exog_test.values if exog_test is not None else None
    n = len(test_vals)

    for i in range(n - horizon + 1):
        try:
            if exog_hist is not None:
                model = ARIMA(history, exog=exog_hist, order=order).fit()
                fc = model.forecast(steps=horizon,
                                    exog=exog_test_vals[i:i + horizon])
            else:
                model = ARIMA(history, order=order).fit()
                fc = model.forecast(steps=horizon)
            preds.append(fc[horizon - 1])
            trues.append(test_vals[i + horizon - 1])
        except Exception:
            preds.append(history[-1])
            trues.append(test_vals[i + horizon - 1])
        # update history dengan nilai aktual (rolling-origin)
        history.append(test_vals[i])
        if exog_hist is not None:
            exog_hist.append(exog_test_vals[i])

    return np.array(trues), np.clip(np.array(preds), 0, None), order
