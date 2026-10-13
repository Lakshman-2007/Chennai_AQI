"""
Ground Monitoring Stations API Router.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.schemas.schemas import StationInfo
from backend.app.data_processing.store import DataStore

router = APIRouter(prefix="/api/stations", tags=["Ground Stations"])

@router.get("", response_model=List[StationInfo])
def get_all_stations():
    """
    Get list of all ground monitoring stations in Chennai with current readings,
    freshness indicators, and official CPCB AQI.
    """
    store = DataStore.get_instance()
    stations = store.get_stations()
    return stations

@router.get("/{station_id}")
def get_station_details(station_id: str):
    """
    Get detailed breakdown for a specific ground station.
    """
    store = DataStore.get_instance()
    detail = store.get_station_detail(station_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found.")
    return detail
