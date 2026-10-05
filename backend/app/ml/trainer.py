"""
Multi-Model Training & Stacking Ensemble Engine for Chennai Air Quality Framework.

Models evaluated:
1. Linear Regression
2. Decision Tree Regressor
3. Random Forest Regressor
4. Extra Trees Regressor
5. Gradient Boosting Regressor
6. XGBoost Regressor
7. LightGBM Regressor
8. CatBoost Regressor
9. Weighted Stacking Meta-Ensemble

Validation strategy: Temporal Train/Val/Test Split + 5-Fold Out-Of-Fold (OOF) Meta-Learning.
"""

import os
import joblib
import json
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
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from backend.app.ml.feature_engineering import engineer_features, PreprocessingPipeline, FEATURE_COLUMNS

class StackingEnsemble:
    """
    Out-Of-Fold Stacking Ensemble combining base regression models.
    """
    def __init__(self, base_models: Dict[str, Any], meta_model: Any = None):
        self.base_models = base_models
        self.meta_model = meta_model or Ridge(alpha=1.0)
        self.weights: Dict[str, float] = {}
        
    def fit_oof(self, X: np.ndarray, y: np.ndarray, n_splits: int = 5):
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        oof_preds = np.zeros((len(X), len(self.base_models)))
        
        model_names = list(self.base_models.keys())
        
        for idx, (name, model) in enumerate(self.base_models.items()):
            for train_idx, val_idx in kf.split(X):
                X_tr, y_tr = X[train_idx], y[train_idx]
                X_val = X[val_idx]
                
                # Fit clone/instance on fold
                model_fold = clone(model)
                model_fold.fit(X_tr, y_tr)
                oof_preds[val_idx, idx] = model_fold.predict(X_val)
                
            # Fit final model on full X
            model.fit(X, y)
            
        # Fit meta learner on OOF predictions
        self.meta_model.fit(oof_preds, y)
        
        # Calculate meta weights
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
    
    # Avoid zero division in MAPE
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
    Trains all candidate models, evaluates performance on temporal split, fits stacking ensemble, and saves artifacts.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Engineer features
    df_feat = engineer_features(df, is_training=True)
    
    # Temporal Train/Test Split (80% train, 20% test)
    split_idx = int(len(df_feat) * 0.8)
    train_df = df_feat.iloc[:split_idx].copy()
    test_df = df_feat.iloc[split_idx:].copy()
    
    pipeline = PreprocessingPipeline(feature_cols=FEATURE_COLUMNS)
    pipeline.fit(train_df)
    
    X_train = pipeline.transform(train_df)
    y_train = train_df[target_col].values
    
    X_test = pipeline.transform(test_df)
    y_test = test_df[target_col].values
    
    # Define Candidate Models
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
    
    comparison_results = []
    trained_models = {}
    
    print("Training base candidate models...")
    for name, model in base_models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = compute_metrics(y_test, y_pred)
        metrics["model"] = name
        comparison_results.append(metrics)
        trained_models[name] = model
        print(f"Model: {name:20s} | R²: {metrics['r2']:.4f} | RMSE: {metrics['rmse']:.2f} | MAE: {metrics['mae']:.2f}")
        
    # Fit Stacking Ensemble
    print("Fitting Stacking Meta-Ensemble...")
    ensemble = StackingEnsemble(base_models=trained_models)
    ensemble.fit_oof(X_train, y_train, n_splits=5)
    
    y_ensemble_pred = ensemble.predict(X_test)
    ens_metrics = compute_metrics(y_test, y_ensemble_pred)
    ens_metrics["model"] = "Ensemble (Stacking)"
    comparison_results.append(ens_metrics)
    print(f"Model: Ensemble (Stacking)  | R²: {ens_metrics['r2']:.4f} | RMSE: {ens_metrics['rmse']:.2f} | MAE: {ens_metrics['mae']:.2f}")
    
    # Save Model Artifacts
    joblib.dump(ensemble, os.path.join(output_dir, "ensemble.pkl"))
    joblib.dump(trained_models["XGBoost"], os.path.join(output_dir, "xgboost.pkl"))
    joblib.dump(trained_models["Random Forest"], os.path.join(output_dir, "random_forest.pkl"))
    joblib.dump(pipeline, os.path.join(output_dir, "pipeline.pkl"))
    
    metadata = {
        "target_variable": target_col,
        "feature_columns": FEATURE_COLUMNS,
        "num_train_samples": len(train_df),
        "num_test_samples": len(test_df),
        "ensemble_weights": ensemble.weights,
        "stations_count": len(df["station_id"].unique()),
        "time_range": {
            "start": str(df["timestamp"].min()),
            "end": str(df["timestamp"].max())
        }
    }
    
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    with open(os.path.join(output_dir, "performance.json"), "w") as f:
        json.dump(comparison_results, f, indent=2)
        
    print("Model training & artifact export complete.")
    return {
        "comparison": comparison_results,
        "ensemble_weights": ensemble.weights,
        "metadata": metadata
    }
