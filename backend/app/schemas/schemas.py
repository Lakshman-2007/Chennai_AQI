"""
Pydantic Schemas for API Requests & Responses.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class Location(BaseModel):
    latitude: float = Field(..., example=13.0827)
    longitude: float = Field(..., example=80.2707)

class PollutantReading(BaseModel):
    value: float
    unit: str = "µg/m³"

class StationInfo(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    zone_type: str
    current_pm25: float
    current_aqi: float
    category: str
    color: str

class AirQualityOverview(BaseModel):
    current_aqi: float
    category: str
    color: str
    health_advisory: str
    dominant_pollutant: str
    last_updated: str
    pollutants: Dict[str, float]
    total_active_stations: int

class PredictionPoint(BaseModel):
    latitude: float
    longitude: float
    predicted_pm25: float
    predicted_pm10: float
    predicted_no2: float
    predicted_so2: float
    predicted_aqi: float
    category: str
    color: str
    confidence_level: str
    uncertainty_pm25: float
    lower_bound_pm25: float
    upper_bound_pm25: float

class SpatialGridResponse(BaseModel):
    grid: List[PredictionPoint]
    total_cells: int
    bounds: Dict[str, float]
    timestamp: str

class HotspotInfo(BaseModel):
    hotspot_id: str
    location_name: str
    center_latitude: float
    center_longitude: float
    peak_pm25: float
    mean_predicted_aqi: float
    category: str
    color: str
    dominant_pollutant: str
    cell_count: int
    confidence: str
    advisory: str

class FeatureImpact(BaseModel):
    feature: str
    name: str
    impact: float
    raw_value: float

class LocalExplanationResponse(BaseModel):
    location: Location
    predicted_pm25: float
    predicted_aqi: float
    base_value: float
    positive_contributors: List[FeatureImpact]
    negative_contributors: List[FeatureImpact]
    narrative: str

class ModelMetric(BaseModel):
    model: str
    r2: float
    rmse: float
    mae: float
    mape: float

class ModelPerformanceResponse(BaseModel):
    best_model: str
    best_r2: float
    best_rmse: float
    best_mae: float
    comparison: List[ModelMetric]
    ensemble_weights: Dict[str, float]
    metadata: Dict[str, Any]

class DataSourceInfo(BaseModel):
    name: str
    type: str
    provider: str
    description: str
    variables: List[str]
    access_method: str
    status: str
