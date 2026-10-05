"""
Pollution Hotspots API Router.
"""

import os
import joblib
from typing import List
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.schemas import HotspotInfo
from backend.app.ml.spatial import generate_chennai_spatial_grid, predict_spatial_grid, detect_pollution_hotspots

router = APIRouter(prefix="/api/hotspots", tags=["Hotspots"])

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))

@router.get("", response_model=List[HotspotInfo])
def get_pollution_hotspots(threshold_pm25: float = Query(60.0, ge=30.0, le=150.0)):
    """
    Identify and cluster high-pollution hotspot zones across Chennai.
    """
    ens_path = os.path.join(MODELS_DIR, "ensemble.pkl")
    pipe_path = os.path.join(MODELS_DIR, "pipeline.pkl")
    
    if not os.path.exists(ens_path) or not os.path.exists(pipe_path):
        raise HTTPException(status_code=500, detail="Model artifacts missing.")
        
    ensemble = joblib.load(ens_path)
    pipeline = joblib.load(pipe_path)
    
    grid_df = generate_chennai_spatial_grid(grid_resolution=25)
    spatial_res = predict_spatial_grid(grid_df, ensemble, pipeline)
    
    hotspots = detect_pollution_hotspots(spatial_res["grid"], pm25_threshold=threshold_pm25)
    return hotspots
