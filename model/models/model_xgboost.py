"""
models/model_xgboost.py - Model 3: XGBoost (Sec. 3.4.3).

Dilatih pada feature matrix penuh (lag, rolling, kalender, eksogen).
Tuning hyperparameter memakai Optuna (TPE), seleksi berdasar RMSE validasi.
"""

import warnings
import numpy as np
import optuna
from xgboost import XGBRegressor

optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore")


def train_xgboost(X_train, y_train, X_val, y_val, params=None, seed=42):
    if params is None:
        params = {}
    model = XGBRegressor(
        n_estimators=params.get("n_estimators", 300),
        max_depth=params.get("max_depth", 5),
        learning_rate=params.get("learning_rate", 0.05),
        subsample=params.get("subsample", 0.9),
        colsample_bytree=params.get("colsample_bytree", 0.9),
        objective="reg:squarederror",
        random_state=seed,
        early_stopping_rounds=50,
        eval_metric="rmse",
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return model


def tune_xgboost(X_train, y_train, X_val, y_val, n_trials=25, seed=42):
    """Bayesian optimization via Optuna; metrik seleksi = RMSE val."""
    def objective(trial):
        params = {
            "n_estimators": trial.suggest_categorical("n_estimators", [100, 300, 500]),
            "max_depth": trial.suggest_categorical("max_depth", [3, 5, 7]),
            "learning_rate": trial.suggest_categorical("learning_rate", [0.01, 0.05, 0.1]),
            "subsample": trial.suggest_categorical("subsample", [0.7, 0.9]),
            "colsample_bytree": trial.suggest_categorical("colsample_bytree", [0.7, 0.9]),
        }
        m = train_xgboost(X_train, y_train, X_val, y_val, params, seed)
        pred = m.predict(X_val)
        return float(np.sqrt(np.mean((y_val - pred) ** 2)))

    study = optuna.create_study(direction="minimize",
                                sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params


def predict_xgboost(model, X):
    return np.clip(model.predict(X), 0, None)
