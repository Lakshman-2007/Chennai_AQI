"""
Ground Monitoring Stations API Router.
"""

import os
import pandas as pd
from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.schemas.schemas import StationInfo
from backend.app.aqi.calculator import calculate_cpcb_aqi, get_aqi_category

router = APIRouter(prefix="/api/stations", tags=["Ground Stations"])

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed", "chennai_multisource_aligned.csv"))

@router.get("", response_model=List[StationInfo])
def get_all_stations():
    """
    Get list of all ground monitoring stations in Chennai with current readings.
    """
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="Dataset not found.")
        
    df = pd.read_csv(DATA_PATH)
    latest_ts = df["timestamp"].max()
    df_latest = df[df["timestamp"] == latest_ts]
    
    stations_list = []
    for idx, row in df_latest.iterrows():
        p_dict = {
            "PM2.5": float(row["ground_pm25"]),
            "PM10": float(row["ground_pm10"]),
            "NO2": float(row["ground_no2"]),
            "SO2": float(row["ground_so2"])
        }
        aqi_res = calculate_cpcb_aqi(p_dict)
        
        stations_list.append({
            "id": str(row["station_id"]),
            "name": str(row["station_name"]),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "zone_type": str(row["zone_type"]),
            "current_pm25": float(row["ground_pm25"]),
            "current_aqi": aqi_res["aqi"],
            "category": aqi_res["category"],
            "color": aqi_res["color"]
        })
        
    return stations_list

@router.get("/{station_id}")
def get_station_details(station_id: str):
    """
    Get detailed breakdown for a specific ground station.
    """
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="Dataset not found.")
        
    df = pd.read_csv(DATA_PATH)
    df_st = df[df["station_id"] == station_id]
    
    if df_st.empty:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found.")
        
    latest_row = df_st.iloc[-1]
    
    p_dict = {
        "PM2.5": float(latest_row["ground_pm25"]),
        "PM10": float(latest_row["ground_pm10"]),
        "NO2": float(latest_row["ground_no2"]),
        "SO2": float(latest_row["ground_so2"]),
        "CO": float(latest_row["ground_co"]),
        "O3": float(latest_row["ground_o3"])
    }
    aqi_res = calculate_cpcb_aqi(p_dict)
    
    return {
        "id": station_id,
        "name": str(latest_row["station_name"]),
        "latitude": float(latest_row["latitude"]),
        "longitude": float(latest_row["longitude"]),
        "zone_type": str(latest_row["zone_type"]),
        "aqi_summary": aqi_res,
        "satellite_features": {
            "satellite_no2": float(latest_row["satellite_no2"]),
            "satellite_so2": float(latest_row["satellite_so2"]),
            "satellite_co": float(latest_row["satellite_co"]),
            "satellite_o3": float(latest_row["satellite_o3"]),
            "aerosol_index": float(latest_row["aerosol_index"])
        },
        "meteorological_conditions": {
            "temperature": float(latest_row["temperature"]),
            "humidity": float(latest_row["relative_humidity"]),
            "wind_speed": float(latest_row["wind_speed"]),
            "wind_direction": float(latest_row["wind_direction"]),
            "pressure": float(latest_row["surface_pressure"]),
            "boundary_layer_height": float(latest_row["boundary_layer_height"])
        },
        "last_updated": str(latest_row["timestamp"])
    }
