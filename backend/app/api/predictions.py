"""
Spatial Predictions API Router.
"""

import os
import joblib
import pandas as pd
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.schemas import SpatialGridResponse, PredictionPoint, Location
from backend.app.ml.spatial import generate_chennai_spatial_grid, predict_spatial_grid
from backend.app.ml.feature_engineering import engineer_features
from backend.app.aqi.calculator import calculate_cpcb_aqi

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))

def _load_model_artifacts():
    ens_path = os.path.join(MODELS_DIR, "ensemble.pkl")
    pipe_path = os.path.join(MODELS_DIR, "pipeline.pkl")
    
    if not os.path.exists(ens_path) or not os.path.exists(pipe_path):
        raise HTTPException(status_code=500, detail="Trained model artifacts missing.")
        
    ensemble = joblib.load(ens_path)
    pipeline = joblib.load(pipe_path)
    return ensemble, pipeline

@router.get("/map", response_model=SpatialGridResponse)
def get_spatial_prediction_map(
    resolution: int = Query(25, ge=10, le=40),
    target_date: Optional[str] = "2026-10-05"
):
    """
    Generate high-resolution spatial prediction grid heatmap over Chennai.
    """
    ensemble, pipeline = _load_model_artifacts()
    grid_df = generate_chennai_spatial_grid(grid_resolution=resolution)
    
    result = predict_spatial_grid(
        grid_df=grid_df,
        ensemble_model=ensemble,
        pipeline=pipeline,
        target_date=target_date
    )
    
    return {
        "grid": result["grid"],
        "total_cells": result["total_cells"],
        "bounds": result["bounds"],
        "timestamp": target_date
    }

@router.post("/point", response_model=PredictionPoint)
def predict_location_point(loc: Location):
    """
    Generate ML prediction and uncertainty bounds for a single coordinate in Chennai.
    """
    ensemble, pipeline = _load_model_artifacts()
    
    single_df = pd.DataFrame([{
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "timestamp": pd.to_datetime("2026-10-05")
    }])
    
    res = predict_spatial_grid(
        grid_df=single_df,
        ensemble_model=ensemble,
        pipeline=pipeline
    )
    
    point = res["grid"][0]
    return point
