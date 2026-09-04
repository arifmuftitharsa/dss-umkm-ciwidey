"""
models/model_prophet.py - Model 2: Prophet (Sec. 3.4.2).

growth linear, seasonality tahunan + mingguan, kalender libur Indonesia
(window H-1..H+2), curah hujan sebagai add_regressor.
"""

import warnings
import logging
import numpy as np
import pandas as pd

logging.getLogger("prophet").setLevel(logging.ERROR)
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from prophet import Prophet
from prophet.make_holidays import make_holidays_df


def _make_id_holidays(years):
    """Kalender libur Indonesia untuk Prophet, window H-1..H+2."""
    h = make_holidays_df(year_list=years, country="ID")
    h["lower_window"] = -1
    h["upper_window"] = 2
    return h


def build_prophet_df(df, use_weather=True):
    """Format dataframe Prophet: ds, y, (regressor cuaca)."""
    out = pd.DataFrame({
        "ds": pd.to_datetime(df["date"].values),
        "y": df["qty_sold"].astype(float).values,
    })
    if use_weather:
        out["rainfall_mm"] = df["rainfall_mm"].astype(float).values
    return out


def fit_prophet(train_df, params, use_weather=True, holidays_df=None):
    m = Prophet(
        growth="linear",
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        holidays=holidays_df,
        changepoint_prior_scale=params.get("changepoint_prior_scale", 0.05),
        seasonality_prior_scale=params.get("seasonality_prior_scale", 10.0),
    )
    if use_weather:
        m.add_regressor("rainfall_mm")
    m.fit(train_df)
    return m


def predict_prophet(model, future_df):
    fc = model.predict(future_df)
    return np.clip(fc["yhat"].values, 0, None)
