"""
Explainable AI (XAI) API Router.
"""

import os
import pandas as pd
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from backend.app.schemas.schemas import LocalExplanationResponse, Location
from backend.app.ml.explainer import AQIExplainer
from backend.app.ml.feature_engineering import engineer_features
from backend.app.ml.model_registry import ModelRegistry
from backend.app.exceptions import ExplainerNotReadyException

router = APIRouter(prefix="/api/explain", tags=["Explainable AI"])

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed", "chennai_multisource_aligned.csv"))

@router.get("/global")
def get_global_explanations():
    """
    Get global SHAP feature importances for all predictive variables across Chennai.
    Conforms to PRD v2.3 Section 4.5.
    """
    registry = ModelRegistry.get_instance()
    if not registry.explainer_ready or registry.xgboost is None:
        raise ExplainerNotReadyException("XAI explainer model unavailable. Explainer artifact is not ready.", code="EXPLAINER_NOT_READY")

    explainer = AQIExplainer(model=registry.xgboost, pipeline=registry.pipeline)

    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="Processed dataset missing.")

    df = pd.read_csv(DATA_PATH).sample(n=min(200, 3185), random_state=42)
    df_feat = engineer_features(df, is_training=False)

    importances = explainer.get_global_feature_importance(df_feat)
    return {
        "global_importance": importances,
        "surrogate_model": "XGBoost Component of Stacking Ensemble",
        "disclaimer": "Feature importances reflect model variance associations, not physical causality."
    }

@router.post("/point", response_model=LocalExplanationResponse)
def get_local_explanation(loc: Location):
    """
    Get local SHAP explanation breakdown and plain-English narrative for a given location.
    Conforms to PRD v2.3 Section 4.6.
    """
    registry = ModelRegistry.get_instance()
    if not registry.explainer_ready or registry.xgboost is None:
        raise ExplainerNotReadyException("XAI explainer model unavailable. Explainer artifact is not ready.", code="EXPLAINER_NOT_READY")

    explainer = AQIExplainer(model=registry.xgboost, pipeline=registry.pipeline)

    now_utc = datetime.now(timezone.utc)
    single_df = pd.DataFrame([{
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "timestamp": now_utc,
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
    }])

    df_feat = engineer_features(single_df, is_training=False)
    local_exp = explainer.explain_instance(df_feat)

    return local_exp
