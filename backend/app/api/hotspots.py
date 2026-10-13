"""
Spatial Pollution Hotspots API Router.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.schemas import HotspotInfo
from backend.app.ml.spatial import generate_chennai_spatial_grid, predict_spatial_grid, detect_chennai_hotspots
from backend.app.ml.model_registry import ModelRegistry

router = APIRouter(prefix="/api/hotspots", tags=["Hotspots"])

@router.get("", response_model=List[HotspotInfo])
def get_chennai_hotspots(
    threshold_pm25: float = Query(55.0, ge=30.0, le=150.0),
    resolution: int = Query(25, ge=15, le=35)
):
    """
    Detect spatial pollution clusters across Chennai using DBSCAN clustering.
    """
    registry = ModelRegistry.get_instance()
    if not registry.is_ready:
        raise HTTPException(status_code=503, detail="Prediction models unavailable.")

    grid_df = generate_chennai_spatial_grid(grid_resolution=resolution)
    res = predict_spatial_grid(
        grid_df=grid_df,
        ensemble_model=registry.ensemble,
        pipeline=registry.pipeline
    )

    hotspots = detect_chennai_hotspots(
        grid_points=res["grid"],
        threshold_pm25=threshold_pm25
    )

    return hotspots
