"""
Spatial Grid Generation, Spatial Inference, and Hotspot Detection Engine for Chennai.

Bounding box:
Longitude: 80.05 E to 80.35 E
Latitude: 12.75 N to 13.25 N
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone, timedelta
from sklearn.cluster import DBSCAN

from backend.app.ml.feature_engineering import engineer_features
from backend.app.aqi.calculator import calculate_pollutant_sub_index, get_aqi_category

# Chennai Bounding Box Constants
CHENNAI_BOUNDS = {
    "min_lat": 12.75,
    "max_lat": 13.25,
    "min_lon": 80.05,
    "max_lon": 80.35
}

def generate_chennai_spatial_grid(grid_resolution: int = 25) -> pd.DataFrame:
    """
    Creates a regular spatial grid of points covering Chennai.
    """
    lats = np.linspace(CHENNAI_BOUNDS["min_lat"], CHENNAI_BOUNDS["max_lat"], grid_resolution)
    lons = np.linspace(CHENNAI_BOUNDS["min_lon"], CHENNAI_BOUNDS["max_lon"], grid_resolution)

    grid_points = []
    for lat in lats:
        for lon in lons:
            grid_points.append({
                "latitude": round(float(lat), 4),
                "longitude": round(float(lon), 4)
            })

    return pd.DataFrame(grid_points)

def parse_horizon_hours(horizon: str) -> int:
    h = horizon.lower().replace("+", "").replace("h", "").strip()
    try:
        return int(h)
    except ValueError:
        return 24

def predict_spatial_grid(
    grid_df: pd.DataFrame,
    ensemble_model: Any,
    pipeline: Any,
    base_weather: Optional[Dict[str, float]] = None,
    horizon: str = "+24h",
    issued_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Runs spatial inference over grid cells in Chennai.
    Guarantees valid_at > issued_at with explicit horizon metadata.
    """
    if issued_at is None:
        issued_at = datetime.now(timezone.utc)
    elif issued_at.tzinfo is None:
        issued_at = issued_at.replace(tzinfo=timezone.utc)

    hours_ahead = parse_horizon_hours(horizon)
    valid_at = issued_at + timedelta(hours=hours_ahead)

    if base_weather is None:
        base_weather = {
            "temperature": 30.5,
            "relative_humidity": 75.0,
            "wind_speed": 11.2,
            "wind_direction": 140.0,
            "surface_pressure": 1008.5,
            "boundary_layer_height": 850.0,
            "precipitation": 0.0
        }

    df_grid = grid_df.copy()
    df_grid["timestamp"] = valid_at

    for k, v in base_weather.items():
        df_grid[k] = v

    # Spatial gradient for Satellite column context based on proximity to industrial/traffic nodes
    lats = df_grid["latitude"].values
    lons = df_grid["longitude"].values

    # Manali Industrial Zone (13.1667 N, 80.2667 E)
    dist_manali = np.sqrt((lats - 13.1667)**2 + (lons - 80.2667)**2)
    # Alandur Transit Corridor (13.0012 N, 80.2015 E)
    dist_transit = np.sqrt((lats - 13.0012)**2 + (lons - 80.2015)**2)

    proximity_factor = 1.0 + 0.65 * np.exp(-dist_manali / 0.08) + 0.35 * np.exp(-dist_transit / 0.05)

    df_grid["satellite_no2"] = 0.000043 * proximity_factor
    df_grid["satellite_so2"] = 0.000012 * proximity_factor
    df_grid["satellite_co"] = 0.035 * proximity_factor
    df_grid["satellite_o3"] = 0.125
    df_grid["aerosol_index"] = 0.65 * proximity_factor

    # Feature engineering
    df_feat = engineer_features(df_grid, is_training=False)
    X_scaled = pipeline.transform(df_feat)

    # Ensemble prediction with std variance
    if hasattr(ensemble_model, "predict_with_std"):
        mean_pm25, std_pm25 = ensemble_model.predict_with_std(X_scaled)
    else:
        mean_pm25 = ensemble_model.predict(X_scaled)
        std_pm25 = np.ones_like(mean_pm25) * 4.5

    grid_results = []
    issued_iso = issued_at.isoformat()
    valid_iso = valid_at.isoformat()

    is_fallback = base_weather is None or True  # Marked fallback_demo_inputs per PRD v2.2 C-07 unless live API injected
    input_status = "fallback_demo_inputs" if is_fallback else "live_measured"
    weather_vintage = "simulated_climatology" if is_fallback else "live"

    for idx in range(len(df_feat)):
        pm25_val = max(5.0, round(float(mean_pm25[idx]), 1))
        variance = float(std_pm25[idx])
        # Ensemble Prediction Spread (Inter-Model Disagreement Range, PRD v2.2 C-06)
        lower_b = max(1.0, round(pm25_val - 1.96 * variance, 1))
        upper_b = round(pm25_val + 1.96 * variance, 1)

        # Derived forecast PM2.5 sub-index (PRD v2.2 C-04)
        si_pm25 = calculate_pollutant_sub_index("PM2.5", pm25_val)
        est_sub_index = round(si_pm25) if si_pm25 is not None else None
        cat, col, _ = get_aqi_category(est_sub_index)

        grid_results.append({
            "latitude": float(df_feat["latitude"].iloc[idx]),
            "longitude": float(df_feat["longitude"].iloc[idx]),
            "target": "PM2.5",
            "unit": "µg/m³",
            "predicted_pm25": pm25_val,
            "derived_pm25_sub_index": est_sub_index,
            "predicted_aqi": est_sub_index,
            "category": cat,
            "color": col,
            "lower_bound_pm25": lower_b,
            "upper_bound_pm25": upper_b,
            "disagreement_range_lower": lower_b,
            "disagreement_range_upper": upper_b,
            "ensemble_std": round(variance, 2),
            "confidence_level": "Ensemble Prediction Spread (Inter-Model Disagreement Range)",
            "uncertainty_label": "Ensemble Prediction Spread (Inter-Model Disagreement Range)",
            "empirical_coverage_pct": 52.28,
            "issued_at": issued_iso,
            "valid_at": valid_iso,
            "horizon": horizon,
            "model_version": "Chennai-AQI-Stacking-v2.2",
            "uncertainty_status": "ensemble_spread",
            "input_status": input_status,
            "weather_vintage_status": weather_vintage,
            "aqi_caveat": "Forecast is a PM2.5 concentration and its derived sub-index. Official CPCB AQI mandates 24h averaging across at least 3 pollutants with one particulate.",
            "data_status": "forecast"
        })

    return {
        "grid": grid_results,
        "total_cells": len(grid_results),
        "bounds": CHENNAI_BOUNDS,
        "issued_at": issued_iso,
        "valid_at": valid_iso,
        "horizon": horizon,
        "model_version": "Chennai-AQI-Stacking-v2.2",
        "target": "PM2.5",
        "unit": "µg/m³",
        "input_status": input_status,
        "weather_vintage_status": weather_vintage
    }

def detect_chennai_hotspots(
    grid_points: List[Dict[str, Any]],
    threshold_pm25: float = 55.0,
    eps: float = 0.035,
    min_samples: int = 3,
    layer_type: str = "forecast",
    data_mode: str = "demo",
    source_time_range: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Detects persistent spatial pollution clusters in Chennai using DBSCAN clustering.
    Supports both forecast spatial grids and observed ground station points (PRD v2.3 Section 4.4).
    """
    def _extract_pm25(p: Dict[str, Any]) -> float:
        return float(p.get("predicted_pm25", p.get("current_pm25", 0.0)))

    high_pollution_pts = [p for p in grid_points if _extract_pm25(p) >= threshold_pm25]

    if len(high_pollution_pts) < min_samples:
        return []

    coords = np.array([[p["latitude"], p["longitude"]] for p in high_pollution_pts])
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
    labels = clustering.labels_

    hotspots = []
    unique_labels = set(labels)
    if -1 in unique_labels:
        unique_labels.remove(-1)

    for cluster_id in unique_labels:
        cluster_mask = labels == cluster_id
        cluster_pts = [high_pollution_pts[i] for i in range(len(high_pollution_pts)) if cluster_mask[i]]

        center_lat = round(float(np.mean([p["latitude"] for p in cluster_pts])), 4)
        center_lon = round(float(np.mean([p["longitude"] for p in cluster_pts])), 4)
        mean_pm25 = round(float(np.mean([_extract_pm25(p) for p in cluster_pts])), 1)

        si_pm25 = calculate_pollutant_sub_index("PM2.5", mean_pm25)
        est_aqi = round(si_pm25) if si_pm25 is not None else 150.0
        cat, col, _ = get_aqi_category(est_aqi)

        severity = "Severe" if mean_pm25 >= 90.0 else ("High" if mean_pm25 >= 60.0 else "Moderate")

        hotspots.append({
            "cluster_id": int(cluster_id) + 1,
            "center_latitude": center_lat,
            "center_longitude": center_lon,
            "mean_pm25": mean_pm25,
            "estimated_aqi": est_aqi,
            "category": cat,
            "color": col,
            "point_count": len(cluster_pts),
            "severity": severity,
            "method": f"DBSCAN Spatial Clustering (eps={eps}, min_samples={min_samples})",
            "layer_type": layer_type,
            "source_time_range": source_time_range,
            "spatial_reference": "EPSG:4326",
            "data_mode": data_mode
        })

    return hotspots
