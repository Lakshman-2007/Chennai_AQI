"""
Spatial Pollution Hotspots API Router.
Conforms to PRD v2.3 Section 4.4:
- Decouples observed data-derived hotspots from ML registry.
- Forecast hotspots require core model readiness (returns 503 if unready).
- Explicit metadata: layer_type, source_time_range, spatial_reference, data_mode.
- No fabricated persistent hotspots on insufficient data.
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from backend.app.schemas.schemas import HotspotInfo
from backend.app.ml.spatial import generate_chennai_spatial_grid, predict_spatial_grid, detect_chennai_hotspots
from backend.app.ml.model_registry import ModelRegistry
from backend.app.data_processing.store import DataStore
from backend.app.exceptions import ModelNotReadyException

router = APIRouter(prefix="/api/hotspots", tags=["Hotspots"])

@router.get("", response_model=List[HotspotInfo])
def get_chennai_hotspots(
    threshold_pm25: float = Query(55.0, ge=30.0, le=150.0),
    resolution: int = Query(25, ge=15, le=35),
    source: str = Query("auto", description="Hotspot source layer: 'auto', 'observed', or 'forecast'")
):
    """
    Detect spatial pollution clusters across Chennai using DBSCAN clustering.
    - 'observed': Directly calculates clusters from valid ground monitor observations without requiring ML registry.
    - 'forecast': Uses prospective ML spatial grid; returns 503 if model is unready.
    - 'auto': Uses forecast if model is ready, else gracefully derives from observed stations.
    """
    registry = ModelRegistry.get_instance()
    store = DataStore.get_instance()
    data_mode = store.get_mode().value

    now_iso = datetime.now(timezone.utc).isoformat()
    time_range = {"start": now_iso, "end": now_iso}

    # Case 1: Explicitly requested observed data-derived hotspots (does not require ML registry)
    if source == "observed":
        stations = store.get_latest_stations()
        station_pts = [
            {
                "latitude": s["latitude"],
                "longitude": s["longitude"],
                "current_pm25": s.get("current_pm25", 0.0)
            }
            for s in stations if s.get("current_pm25") is not None
        ]
        hotspots = detect_chennai_hotspots(
            grid_points=station_pts,
            threshold_pm25=threshold_pm25,
            eps=0.08,
            min_samples=2,
            layer_type="observed",
            data_mode=data_mode,
            source_time_range=time_range
        )
        return hotspots

    # Case 2: Explicitly requested forecast hotspots
    if source == "forecast":
        if not registry.core_model_ready:
            raise ModelNotReadyException(
                detail="Forecast hotspots unavailable: core prediction model is not ready.",
                code="MODEL_NOT_READY"
            )
        grid_df = generate_chennai_spatial_grid(grid_resolution=resolution)
        res = predict_spatial_grid(
            grid_df=grid_df,
            ensemble_model=registry.ensemble,
            pipeline=registry.pipeline
        )
        hotspots = detect_chennai_hotspots(
            grid_points=res["grid"],
            threshold_pm25=threshold_pm25,
            eps=0.035,
            min_samples=3,
            layer_type="forecast",
            data_mode=data_mode,
            source_time_range=time_range
        )
        return hotspots

    # Case 3: Auto mode (default)
    if registry.core_model_ready:
        grid_df = generate_chennai_spatial_grid(grid_resolution=resolution)
        res = predict_spatial_grid(
            grid_df=grid_df,
            ensemble_model=registry.ensemble,
            pipeline=registry.pipeline
        )
        hotspots = detect_chennai_hotspots(
            grid_points=res["grid"],
            threshold_pm25=threshold_pm25,
            eps=0.035,
            min_samples=3,
            layer_type="forecast",
            data_mode=data_mode,
            source_time_range=time_range
        )
        return hotspots
    else:
        # Fallback to observed ground station observations when ML model is disabled/unready
        stations = store.get_latest_stations()
        station_pts = [
            {
                "latitude": s["latitude"],
                "longitude": s["longitude"],
                "current_pm25": s.get("current_pm25", 0.0)
            }
            for s in stations if s.get("current_pm25") is not None
        ]
        hotspots = detect_chennai_hotspots(
            grid_points=station_pts,
            threshold_pm25=threshold_pm25,
            eps=0.08,
            min_samples=2,
            layer_type="observed",
            data_mode=data_mode,
            source_time_range=time_range
        )
        return hotspots
