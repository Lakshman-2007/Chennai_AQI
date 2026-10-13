"""
Air Quality API Endpoints.
Integrates DataStore, CPCB calculation, and data export endpoints.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response
from backend.app.schemas.schemas import AirQualityOverview
from backend.app.data_processing.store import DataStore

router = APIRouter(prefix="/api", tags=["Air Quality"])

@router.get("/overview", response_model=AirQualityOverview)
def get_air_quality_overview():
    """
    Get current citywide air quality overview for Chennai with CPCB NAQI calculation,
    eligibility status, data freshness, and data mode indicators.
    """
    store = DataStore.get_instance()
    overview = store.get_overview()
    if not overview:
        raise HTTPException(status_code=503, detail="Air quality overview data unavailable.")
    return overview

@router.get("/air-quality/history")
def get_air_quality_history(
    days: int = Query(30, ge=1, le=365),
    station_id: Optional[str] = None
):
    """
    Get historical air quality time series for trend analytics and chart plotting.
    """
    store = DataStore.get_instance()
    res = store.get_history(days=days, station_id=station_id)
    return res

@router.get("/export")
def export_air_quality_data(
    format: str = Query("csv", pattern="^(csv|json)$"),
    days: int = Query(30, ge=1, le=365),
    station_id: Optional[str] = None
):
    """
    Export filtered observations and analytics with provenance metadata (FR-23).
    """
    store = DataStore.get_instance()
    data = store.get_history(days=days, station_id=station_id)

    if format == "json":
        return {
            "metadata": {
                "system": "Chennai Air Quality Intelligence Platform",
                "export_format": "JSON",
                "days_included": days,
                "station_filter": station_id or "all_stations",
                "data_mode": data["data_mode"],
                "data_status": data["data_status"]
            },
            "records": data["history"]
        }

    # Format as CSV
    import io
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "timestamp", "station_id", "pm25_ug_m3", "pm10_ug_m3", "no2_ug_m3", "so2_ug_m3",
        "aqi", "aqi_category", "temperature_c", "humidity_pct", "wind_speed_kmh", "data_status"
    ])

    for row in data["history"]:
        writer.writerow([
            row["timestamp"],
            data["station_id"],
            row["pm25"],
            row["pm10"],
            row["no2"],
            row["so2"],
            row["aqi"],
            row["category"],
            row["temperature"],
            row["humidity"],
            row["wind_speed"],
            data["data_status"]
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=chennai_aqi_export_{days}d.csv"}
    )
