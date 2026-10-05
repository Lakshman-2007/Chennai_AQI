"""
Air Quality API Endpoints.
"""

from typing import Optional
import os
from datetime import datetime
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.schemas import AirQualityOverview
from backend.app.aqi.calculator import calculate_cpcb_aqi

router = APIRouter(prefix="/api", tags=["Air Quality"])

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed", "chennai_multisource_aligned.csv"))

@router.get("/overview", response_model=AirQualityOverview)
def get_air_quality_overview():
    """
    Get current citywide air quality overview for Chennai.
    """
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="Processed dataset not found.")
        
    df = pd.read_csv(DATA_PATH)
    latest_ts = df["timestamp"].max()
    df_latest = df[df["timestamp"] == latest_ts]
    
    mean_pm25 = round(float(df_latest["ground_pm25"].mean()), 1)
    mean_pm10 = round(float(df_latest["ground_pm10"].mean()), 1)
    mean_no2 = round(float(df_latest["ground_no2"].mean()), 1)
    mean_so2 = round(float(df_latest["ground_so2"].mean()), 1)
    mean_co = round(float(df_latest["ground_co"].mean()), 2)
    mean_o3 = round(float(df_latest["ground_o3"].mean()), 1)
    
    pollutants = {
        "PM2.5": mean_pm25,
        "PM10": mean_pm10,
        "NO2": mean_no2,
        "SO2": mean_so2,
        "CO": mean_co,
        "O3": mean_o3
    }
    
    aqi_res = calculate_cpcb_aqi(pollutants)
    
    return {
        "current_aqi": aqi_res["aqi"],
        "category": aqi_res["category"],
        "color": aqi_res["color"],
        "health_advisory": aqi_res["health_advisory"],
        "dominant_pollutant": aqi_res["dominant_pollutant"],
        "last_updated": str(latest_ts),
        "pollutants": pollutants,
        "total_active_stations": len(df_latest)
    }

@router.get("/air-quality/history")
def get_air_quality_history(
    days: int = Query(30, ge=1, le=365),
    station_id: Optional[str] = None
):
    """
    Get historical air quality time series for trend visualization.
    """
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="Processed dataset not found.")
        
    df = pd.read_csv(DATA_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    if station_id:
        df = df[df["station_id"] == station_id]
        
    max_date = df["timestamp"].max()
    start_date = max_date - pd.Timedelta(days=days)
    
    df_filtered = df[df["timestamp"] >= start_date]
    
    # Group by date
    grouped = df_filtered.groupby("timestamp").agg({
        "ground_pm25": "mean",
        "ground_pm10": "mean",
        "ground_no2": "mean",
        "ground_so2": "mean",
        "temperature": "mean",
        "relative_humidity": "mean",
        "wind_speed": "mean",
        "satellite_no2": "mean",
        "aerosol_index": "mean"
    }).reset_index()
    
    history_records = []
    for idx, row in grouped.iterrows():
        p_dict = {
            "PM2.5": round(float(row["ground_pm25"]), 1),
            "PM10": round(float(row["ground_pm10"]), 1),
            "NO2": round(float(row["ground_no2"]), 1),
            "SO2": round(float(row["ground_so2"]), 1)
        }
        aqi_res = calculate_cpcb_aqi(p_dict)
        
        history_records.append({
            "timestamp": row["timestamp"].strftime("%Y-%m-%d"),
            "pm25": p_dict["PM2.5"],
            "pm10": p_dict["PM10"],
            "no2": p_dict["NO2"],
            "so2": p_dict["SO2"],
            "aqi": aqi_res["aqi"],
            "category": aqi_res["category"],
            "temperature": round(float(row["temperature"]), 1),
            "humidity": round(float(row["relative_humidity"]), 1),
            "wind_speed": round(float(row["wind_speed"]), 1),
            "satellite_no2": float(row["satellite_no2"]),
            "aerosol_index": float(row["aerosol_index"])
        })
        
    return {
        "days": days,
        "station_id": station_id or "all_stations_avg",
        "history": history_records
    }
