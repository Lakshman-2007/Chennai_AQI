"""
Explainable AI (XAI) API Router.
"""

import os
import joblib
import pandas as pd
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException
from backend.app.schemas.schemas import LocalExplanationResponse, Location
from backend.app.ml.explainer import AQIExplainer
from backend.app.ml.feature_engineering import engineer_features
from backend.app.ml.spatial import predict_spatial_grid

router = APIRouter(prefix="/api/explain", tags=["Explainable AI"])

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed", "chennai_multisource_aligned.csv"))

def _get_explainer():
    xgb_path = os.path.join(MODELS_DIR, "xgboost.pkl")
    pipe_path = os.path.join(MODELS_DIR, "pipeline.pkl")
    
    if not os.path.exists(xgb_path) or not os.path.exists(pipe_path):
        raise HTTPException(status_code=500, detail="XGBoost model artifact missing for XAI.")
        
    model = joblib.load(xgb_path)
    pipeline = joblib.load(pipe_path)
    return AQIExplainer(model=model, pipeline=pipeline), pipeline

@router.get("/global")
def get_global_explanations():
    """
    Get global SHAP feature importances for all predictive variables.
    """
    explainer, pipeline = _get_explainer()
    
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="Dataset missing.")
        
    df = pd.read_csv(DATA_PATH).sample(n=200, random_state=42)
    df_feat = engineer_features(df, is_training=False)
    
    importances = explainer.get_global_feature_importance(df_feat)
    return {
        "global_importance": importances
    }

@router.post("/point", response_model=LocalExplanationResponse)
def get_local_explanation(loc: Location):
    """
    Get local SHAP explanation breakdown and plain-English narrative for a given location.
    """
    explainer, pipeline = _get_explainer()
    ens_path = os.path.join(MODELS_DIR, "ensemble.pkl")
    ensemble = joblib.load(ens_path)
    
    single_df = pd.DataFrame([{
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "timestamp": pd.to_datetime("2026-10-05")
    }])
    
    base_weather = {
        "temperature": 30.5,
        "relative_humidity": 75.0,
        "wind_speed": 11.2,
        "wind_direction": 140.0,
        "surface_pressure": 1008.5,
        "boundary_layer_height": 850.0,
        "precipitation": 0.0,
        "satellite_no2": 0.000043,
        "satellite_so2": 0.000012,
        "satellite_co": 0.035,
        "satellite_o3": 0.125,
        "aerosol_index": 0.65
    }
    for k, v in base_weather.items():
        single_df[k] = v
        
    df_feat = engineer_features(single_df, is_training=False)
    
    local_exp = explainer.explain_instance(df_feat)
    
    spatial_res = predict_spatial_grid(single_df, ensemble, pipeline)
    point = spatial_res["grid"][0]

    return {
        "location": loc,
        "predicted_pm25": point["predicted_pm25"],
        "predicted_aqi": point["predicted_aqi"],
        "base_value": local_exp["base_value"],
        "positive_contributors": local_exp["positive_contributors"],
        "negative_contributors": local_exp["negative_contributors"],
        "narrative": local_exp["narrative"]
    }
