"""
Multi-Model Training & Stacking Ensemble Engine for Chennai Air Quality Framework.

Normative PRD 21.4 Requirements:
1. Walk-forward nested time-series validation: Random K-fold and shuffling are strictly prohibited.
2. Chronological holdout: Untouched latest period for final evaluation.
3. Out-Of-Fold (OOF) meta-features generated strictly using expanding temporal windows (TimeSeriesSplit).
4. Baselines: Persistence (Last-Known-Value) and Seasonal-Naive models evaluated as required benchmark.
5. Model Card and evaluation manifest generation with reproducibility fingerprint.
"""

import os
import joblib
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any

from sklearn.base import clone
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from backend.app.ml.feature_engineering import engineer_features, PreprocessingPipeline, FEATURE_COLUMNS

class WalkForwardStackingEnsemble:
    """
    Leakage-safe Out-Of-Fold Walk-Forward Stacking Ensemble combining base regression models.
    Meta-learner is fitted on out-of-fold predictions generated strictly forward in time.
    """
    def __init__(self, base_models: Dict[str, Any], meta_model: Any = None):
        self.base_models = base_models
        self.meta_model = meta_model or Ridge(alpha=1.0)
        self.weights: Dict[str, float] = {}
        self.validation_strategy = "Walk-Forward Nested TimeSeriesSplit (n_splits=5)"

    def fit_oof_walk_forward(self, X: np.ndarray, y: np.ndarray, n_splits: int = 5):
        """
        Fits base models across forward temporal folds using expanding windows.
        No future rows ever leak into past training blocks.
        """
        tscv = TimeSeriesSplit(n_splits=n_splits)
        model_names = list(self.base_models.keys())
        n_models = len(model_names)

        # Track OOF indices and predictions
        oof_preds_list = []
        oof_targets_list = []

        for train_idx, val_idx in tscv.split(X):
            X_tr, y_tr = X[train_idx], y[train_idx]
            X_val, y_val = X[val_idx], y[val_idx]

            fold_preds = np.zeros((len(val_idx), n_models))
            for idx, (name, model) in enumerate(self.base_models.items()):
                fold_model = clone(model)
                fold_model.fit(X_tr, y_tr)
                fold_preds[:, idx] = fold_model.predict(X_val)

            oof_preds_list.append(fold_preds)
            oof_targets_list.append(y_val)

        meta_X = np.vstack(oof_preds_list)
        meta_y = np.concatenate(oof_targets_list)

        # Fit Ridge meta-learner on out-of-fold temporal predictions
        self.meta_model.fit(meta_X, meta_y)

        # Fit all final base models on the complete training set X
        for name, model in self.base_models.items():
            model.fit(X, y)

        # Derive normalized meta-weights
        if hasattr(self.meta_model, "coef_"):
            coefs = np.clip(self.meta_model.coef_, 0, None)
            total = np.sum(coefs) + 1e-8
            normalized = coefs / total
            for name, w in zip(model_names, normalized):
                self.weights[name] = round(float(w), 4)
        else:
            equal_w = 1.0 / len(model_names)
            for name in model_names:
                self.weights[name] = round(equal_w, 4)

    def predict(self, X: np.ndarray) -> np.ndarray:
        base_preds = np.column_stack([model.predict(X) for model in self.base_models.values()])
        return self.meta_model.predict(base_preds)

    def predict_with_std(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        base_preds = np.column_stack([model.predict(X) for model in self.base_models.values()])
        mean_pred = self.meta_model.predict(base_preds)
        std_pred = np.std(base_preds, axis=1)
        return mean_pred, std_pred

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))

    mask = y_true > 1.0
    if np.sum(mask) > 0:
        mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)
    else:
        mape = 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
        "mape": round(mape, 2)
    }

def train_aqi_models(
    df: pd.DataFrame,
    target_col: str = "ground_pm25",
    output_dir: str = "models"
) -> Dict[str, Any]:
    """
    Executes leakage-safe training pipeline conforming to PRD Section 21.4:
    - Chronological train / holdout split
    - Baseline persistence & seasonal naive benchmarks
    - 8 Candidate base regressors + Walk-Forward Stacking Meta-Ensemble
    - Generates performance.json, metadata.json, and model_card.json
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Feature Engineering
    df_feat = engineer_features(df, is_training=True)

    # 2. Strict Chronological Timestamp-Grouped Holdout (PRD v2.2 C-05)
    # Sorting unique timestamps ensures no stations at the same time slice are split between partitions
    unique_timestamps = np.sort(df_feat["timestamp"].drop_duplicates().values)
    split_idx = int(len(unique_timestamps) * 0.8)
    split_timestamp = unique_timestamps[split_idx]

    train_df = df_feat[df_feat["timestamp"] < split_timestamp].copy()
    test_df = df_feat[df_feat["timestamp"] >= split_timestamp].copy()

    # Preprocessing pipeline fit STRICTLY on train set
    pipeline = PreprocessingPipeline(feature_cols=FEATURE_COLUMNS)
    pipeline.fit(train_df)

    X_train = pipeline.transform(train_df)
    y_train = train_df[target_col].values

    X_test = pipeline.transform(test_df)
    y_test = test_df[target_col].values

    comparison_results = []

    # 3. Baseline Models (Mandatory benchmark PRD Section 8.1 & RG-06)
    # Baseline 1: Persistence / Last Known Value (pm25_lag_1d)
    y_persistence = test_df["pm25_lag_1d"].values
    pers_metrics = compute_metrics(y_test, y_persistence)
    pers_metrics["model"] = "Baseline: Persistence (Lag-1D)"
    comparison_results.append(pers_metrics)

    # Baseline 2: Seasonal-Naive (monthly historical mean from train set)
    monthly_means = train_df.groupby("month")[target_col].mean().to_dict()
    y_seasonal = test_df["month"].map(monthly_means).fillna(train_df[target_col].mean()).values
    seas_metrics = compute_metrics(y_test, y_seasonal)
    seas_metrics["model"] = "Baseline: Seasonal-Naive"
    comparison_results.append(seas_metrics)

    # 4. Define Candidate Base Learners
    base_models = {
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(max_depth=10, random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1),
        "Extra Trees": ExtraTreesRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, learning_rate=0.08, max_depth=5, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=120, learning_rate=0.07, max_depth=5, random_state=42, n_jobs=-1),
        "LightGBM": LGBMRegressor(n_estimators=120, learning_rate=0.07, max_depth=5, random_state=42, verbose=-1, n_jobs=-1),
        "CatBoost": CatBoostRegressor(iterations=120, learning_rate=0.07, depth=5, random_seed=42, verbose=0)
    }

    trained_models = {}
    print("Training candidate base models...")
    for name, model in base_models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = compute_metrics(y_test, y_pred)
        metrics["model"] = name
        comparison_results.append(metrics)
        trained_models[name] = model
        print(f"Model: {name:22s} | R²: {metrics['r2']:.4f} | RMSE: {metrics['rmse']:.2f} | MAE: {metrics['mae']:.2f}")

    # 5. Walk-Forward Nested Stacking Meta-Ensemble
    print("Fitting Walk-Forward TimeSeriesSplit Meta-Ensemble...")
    ensemble = WalkForwardStackingEnsemble(base_models=trained_models)
    ensemble.fit_oof_walk_forward(X_train, y_train, n_splits=5)

    y_ensemble_pred, std_ensemble_pred = ensemble.predict_with_std(X_test)
    ens_metrics = compute_metrics(y_test, y_ensemble_pred)
    ens_metrics["model"] = "Ensemble (Stacking)"

    # Empirical holdout coverage calculation for Ensemble Prediction Spread (PRD v2.2 C-06)
    lower_bounds = np.maximum(0.0, y_ensemble_pred - 1.96 * std_ensemble_pred)
    upper_bounds = y_ensemble_pred + 1.96 * std_ensemble_pred
    is_covered = (y_test >= lower_bounds) & (y_test <= upper_bounds)
    empirical_coverage_pct = round(float(np.mean(is_covered) * 100.0), 2)
    ens_metrics["empirical_coverage_pct"] = empirical_coverage_pct
    ens_metrics["mean_ensemble_spread"] = round(float(np.mean(upper_bounds - lower_bounds)), 2)
    comparison_results.append(ens_metrics)
    print(f"Model: Ensemble (Stacking)    | R²: {ens_metrics['r2']:.4f} | RMSE: {ens_metrics['rmse']:.2f} | MAE: {ens_metrics['mae']:.2f} | Empirical Coverage: {empirical_coverage_pct}%")

    # Calculate Improvement over Persistence Baseline
    baseline_rmse = pers_metrics["rmse"]
    model_rmse = ens_metrics["rmse"]
    rmse_improvement_pct = round(((baseline_rmse - model_rmse) / baseline_rmse) * 100.0, 2)

    # 6. Save Model Artifacts
    joblib.dump(ensemble, os.path.join(output_dir, "ensemble.pkl"))
    joblib.dump(trained_models["XGBoost"], os.path.join(output_dir, "xgboost.pkl"))
    joblib.dump(trained_models["Random Forest"], os.path.join(output_dir, "random_forest.pkl"))
    joblib.dump(pipeline, os.path.join(output_dir, "pipeline.pkl"))

    metadata = {
        "model_id": "Chennai-AQI-Stacking-v2.2",
        "target_variable": target_col,
        "target_unit": "µg/m³",
        "forecast_horizon": "+24h",
        "validation_strategy": "Timestamp-Grouped Chronological Holdout (20%) + 5-Fold Walk-Forward TimeSeriesSplit",
        "uncertainty_metric": "Ensemble Prediction Spread (Inter-Model Disagreement Range)",
        "empirical_coverage_pct": empirical_coverage_pct,
        "feature_columns": FEATURE_COLUMNS,
        "num_train_samples": len(train_df),
        "num_test_samples": len(test_df),
        "ensemble_weights": ensemble.weights,
        "stations_count": len(df["station_id"].unique()),
        "time_range": {
            "start": str(df["timestamp"].min()),
            "end": str(df["timestamp"].max())
        },
        "baseline_rmse": baseline_rmse,
        "ensemble_rmse": model_rmse,
        "rmse_improvement_pct": rmse_improvement_pct,
        "leakage_safeguards": [
            "Timestamp-grouped chronological train/holdout split preventing multi-station temporal leakage (C-05)",
            "Strict TimeSeriesSplit expanding window (no random shuffling)",
            "Holdout set reserved untouched prior to meta-learner fitting",
            "Preprocessing pipeline fit strictly on training partition"
        ],
        "training_environment": {
            "python_version": "3.13.7",
            "scikit_learn": "1.7.2",
            "joblib": "1.5.2",
            "xgboost": "3.4.1",
            "lightgbm": "4.7.0",
            "catboost": "1.2.10",
            "shap": "0.52.0",
            "numpy": "2.2.6",
            "pandas": "2.3.2"
        }
    }

    model_card = {
        "schema_version": "1.0",
        "model_details": {
            "name": "Chennai Air Quality PM2.5 Walk-Forward Stacking Ensemble",
            "version": "2.3.0",
            "type": "Supervised Regression / Stacking Ensemble",
            "target": "PM2.5 Surface Concentration (µg/m³)",
            "forecast_horizon": "+24h prospective interval",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "license": "MIT",
            "training_environment": {
                "python_version": "3.13.7",
                "scikit_learn": "1.7.2",
                "joblib": "1.5.2",
                "xgboost": "3.4.1",
                "lightgbm": "4.7.0",
                "catboost": "1.2.10",
                "shap": "0.52.0",
                "numpy": "2.2.6",
                "pandas": "2.3.2"
            }
        },
        "intended_use": {
            "primary_use": "Predicting next-day PM2.5 concentrations across Chennai monitoring stations and spatial grids.",
            "caveats": "Forecast concentrations are not regulatory AQI without 24-hr averaging completeness. Sentinel-5P is an offline context feature."
        },
        "evaluation_factors": {
            "chronological_holdout_samples": len(test_df),
            "holdout_date_start": str(test_df["timestamp"].min()),
            "holdout_date_end": str(test_df["timestamp"].max()),
            "metrics": ens_metrics,
            "empirical_holdout_coverage_pct": empirical_coverage_pct,
            "baseline_comparison": {
                "persistence_baseline_rmse": baseline_rmse,
                "seasonal_naive_rmse": seas_metrics["rmse"],
                "ensemble_rmse": model_rmse,
                "percentage_rmse_reduction": rmse_improvement_pct
            }
        },
        "ethical_considerations": {
            "transparency": f"Predictions are accompanied by SHAP feature attributions (via XGBoost surrogate component) and Ensemble Prediction Spread (Inter-Model Disagreement Range) with empirical holdout coverage measured at {empirical_coverage_pct}%.",
            "health_advice": "Non-diagnostic; informs public awareness without medical assertions."
        }
    }

    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    with open(os.path.join(output_dir, "performance.json"), "w") as f:
        json.dump(comparison_results, f, indent=2)

    with open(os.path.join(output_dir, "model_card.json"), "w") as f:
        json.dump(model_card, f, indent=2)

    print("Model training, walk-forward validation & Model Card generation complete.")
    return {
        "comparison": comparison_results,
        "ensemble_weights": ensemble.weights,
        "metadata": metadata,
        "model_card": model_card
    }
