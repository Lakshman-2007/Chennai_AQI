"""
Spatial Grid Generation, Spatial Inference, and Hotspot Detection Engine for Chennai.

Bounding box:
Longitude: 80.05 E to 80.35 E
Latitude: 12.75 N to 13.25 N
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from sklearn.cluster import DBSCAN

from backend.app.ml.feature_engineering import engineer_features
from backend.app.aqi.calculator import calculate_cpcb_aqi, get_aqi_category

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

def predict_spatial_grid(
    grid_df: pd.DataFrame,
    ensemble_model: Any,
    pipeline: Any,
    base_weather: Dict[str, float] = None,
    target_date: str = "2026-10-05"
) -> Dict[str, Any]:
    """
    Runs spatial inference over every grid cell in Chennai using satellite + meteorological features.
    """
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
    df_grid["timestamp"] = pd.to_datetime(target_date)
    
    for k, v in base_weather.items():
        df_grid[k] = v
        
    # Spatial gradient for Satellite NO2 & SO2 columns based on proximity to industrial / traffic hubs
    lats = df_grid["latitude"].values
    lons = df_grid["longitude"].values
    
    # Distance to Manali Industrial Zone (13.1667 N, 80.2667 E)
    dist_manali = np.sqrt((lats - 13.1667)**2 + (lons - 80.2667)**2)
    # Distance to Transit Corridor (13.0012 N, 80.2015 E)
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
    
    # Ensemble prediction with std variance (uncertainty)
    if hasattr(ensemble_model, "predict_with_std"):
        mean_pm25, std_pm25 = ensemble_model.predict_with_std(X_scaled)
    else:
        mean_pm25 = ensemble_model.predict(X_scaled)
        std_pm25 = np.ones_like(mean_pm25) * 3.5
        
    grid_results = []
    
    for idx in range(len(df_feat)):
        pm25_val = max(5.0, round(float(mean_pm25[idx]), 1))
        uncertainty = round(float(std_pm25[idx]), 1)
        
        # Derive Multi-pollutant estimations
        pm10_val = round(pm25_val * 1.65, 1)
        no2_val = round(pm25_val * 0.45, 1)
        so2_val = round(pm25_val * 0.25, 1)
        
        aqi_res = calculate_cpcb_aqi({
            "PM2.5": pm25_val,
            "PM10": pm10_val,
            "NO2": no2_val,
            "SO2": so2_val
        })
        
        lower_bound = max(0.0, round(pm25_val - 1.96 * uncertainty, 1))
        upper_bound = round(pm25_val + 1.96 * uncertainty, 1)
        
        grid_results.append({
            "latitude": float(df_feat["latitude"].iloc[idx]),
            "longitude": float(df_feat["longitude"].iloc[idx]),
            "predicted_pm25": pm25_val,
            "predicted_pm10": pm10_val,
            "predicted_no2": no2_val,
            "predicted_so2": so2_val,
            "predicted_aqi": aqi_res["aqi"],
            "category": aqi_res["category"],
            "color": aqi_res["color"],
            "confidence_level": "High" if uncertainty < 4.0 else ("Medium" if uncertainty < 7.0 else "Low"),
            "uncertainty_pm25": uncertainty,
            "lower_bound_pm25": lower_bound,
            "upper_bound_pm25": upper_bound
        })
        
    return {
        "grid": grid_results,
        "total_cells": len(grid_results),
        "bounds": CHENNAI_BOUNDS
    }

def detect_pollution_hotspots(grid_results: List[Dict[str, Any]], pm25_threshold: float = 60.0) -> List[Dict[str, Any]]:
    """
    Identifies high-pollution hotspot zones across Chennai using spatial clustering.
    """
    high_poll_cells = [cell for cell in grid_results if cell["predicted_pm25"] >= pm25_threshold]
    
    if not high_poll_cells:
        return []
        
    coords = np.array([[c["latitude"], c["longitude"]] for c in high_poll_cells])
    
    # DBSCAN spatial clustering (eps ~ 0.05 degrees approx 5.5 km)
    db = DBSCAN(eps=0.05, min_samples=2).fit(coords)
    labels = db.labels_
    
    hotspots = []
    
    unique_labels = set(labels)
    for label in unique_labels:
        if label == -1:
            continue
            
        cluster_mask = (labels == label)
        cluster_cells = [high_poll_cells[i] for i in range(len(high_poll_cells)) if cluster_mask[i]]
        
        avg_lat = round(float(np.mean([c["latitude"] for c in cluster_cells])), 4)
        avg_lon = round(float(np.mean([c["longitude"] for c in cluster_cells])), 4)
        max_pm25 = round(float(np.max([c["predicted_pm25"] for c in cluster_cells])), 1)
        avg_aqi = round(float(np.mean([c["predicted_aqi"] for c in cluster_cells])), 1)
        
        cat_name, hex_color, advisory = get_aqi_category(avg_aqi)
        
        # Name location region based on coordinates
        location_name = "North Chennai Industrial Zone" if avg_lat > 13.12 else ("Central Transit Corridor" if avg_lat > 13.00 else "South-East Urban Cluster")
        
        hotspots.append({
            "hotspot_id": f"hotspot_{label + 1}",
            "location_name": location_name,
            "center_latitude": avg_lat,
            "center_longitude": avg_lon,
            "peak_pm25": max_pm25,
            "mean_predicted_aqi": avg_aqi,
            "category": cat_name,
            "color": hex_color,
            "dominant_pollutant": "PM2.5",
            "cell_count": len(cluster_cells),
            "confidence": "High",
            "advisory": advisory
        })
        
    hotspots.sort(key=lambda x: x["mean_predicted_aqi"], reverse=True)
    return hotspots
