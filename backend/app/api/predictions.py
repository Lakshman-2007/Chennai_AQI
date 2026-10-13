"""
Spatial Predictions & Future Forecasting API Router.
"""

from typing import Optional
from datetime import datetime, timezone
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.schemas import SpatialGridResponse, PredictionPoint, ForecastRequest
from backend.app.ml.spatial import generate_chennai_spatial_grid, predict_spatial_grid
from backend.app.ml.model_registry import ModelRegistry

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

@router.get("/map", response_model=SpatialGridResponse)
def get_spatial_prediction_map(
    resolution: int = Query(25, ge=10, le=40),
    horizon: str = Query("+24h", description="Forecast horizon (+1h, +6h, +12h, +24h)")
):
    """
    Generate high-resolution spatial prediction grid heatmap over Chennai for specified horizon.
    """
    registry = ModelRegistry.get_instance()
    if not registry.is_ready:
        raise HTTPException(status_code=503, detail=f"Prediction service unavailable: {registry.error_message}")

    grid_df = generate_chennai_spatial_grid(grid_resolution=resolution)

    result = predict_spatial_grid(
        grid_df=grid_df,
        ensemble_model=registry.ensemble,
        pipeline=registry.pipeline,
        horizon=horizon,
        issued_at=datetime.now(timezone.utc)
    )

    return result

@router.post("/point", response_model=PredictionPoint)
def predict_location_point(req: ForecastRequest):
    """
    Generate ML prediction and calibrated 95% confidence intervals for a coordinate in Chennai.
    Guarantees valid_at > issued_at.
    """
    registry = ModelRegistry.get_instance()
    if not registry.is_ready:
        raise HTTPException(status_code=503, detail=f"Prediction service unavailable: {registry.error_message}")

    now_utc = datetime.now(timezone.utc)
    single_df = pd.DataFrame([{
        "latitude": req.latitude,
        "longitude": req.longitude,
        "timestamp": now_utc
    }])

    res = predict_spatial_grid(
        grid_df=single_df,
        ensemble_model=registry.ensemble,
        pipeline=registry.pipeline,
        horizon=req.horizon,
        issued_at=now_utc
    )

    point = res["grid"][0]
    return point
