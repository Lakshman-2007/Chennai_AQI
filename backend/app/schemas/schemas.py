"""
Pydantic Schemas for Chennai Air Quality Framework API Contracts.
Fully compliant with Pydantic V2 and PRD Sections 10, 11, and 21.8.
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

VALID_HORIZONS = {"+1h", "+6h", "+12h", "+24h", "+48h"}

def normalize_horizon(v: Any) -> str:
    if isinstance(v, str):
        norm = v.strip()
        if not norm.startswith("+") and f"+{norm}" in VALID_HORIZONS:
            norm = f"+{norm}"
        if norm in VALID_HORIZONS:
            return norm
    raise ValueError(f"Invalid forecast horizon '{v}'. Allowed horizons are: {sorted(list(VALID_HORIZONS))}")

class Location(BaseModel):
    latitude: float = Field(ge=12.5, le=13.5, description="Latitude in Chennai bounding box")
    longitude: float = Field(ge=79.8, le=80.6, description="Longitude in Chennai bounding box")

class ForecastRequest(BaseModel):
    latitude: float = Field(ge=12.5, le=13.5, description="Latitude in Chennai region")
    longitude: float = Field(ge=79.8, le=80.6, description="Longitude in Chennai region")
    horizon: str = Field(default="+24h", description="Forecast horizon (+1h, +6h, +12h, +24h, +48h)")

    @field_validator("horizon", mode="before")
    @classmethod
    def check_horizon(cls, v: Any) -> str:
        return normalize_horizon(v)

class AirQualityOverview(BaseModel):
    current_aqi: Optional[float]
    category: str
    color: str
    health_advisory: str
    dominant_pollutant: Optional[str]
    last_updated: Optional[str]
    pollutants: Dict[str, Optional[float]]
    sub_indices: Optional[Dict[str, float]] = None
    total_active_stations: int
    data_mode: str = "demo"
    data_status: str = "synthetic"
    freshness: str = "stale"
    age_seconds: Optional[float] = None
    is_synthetic: bool = True
    eligible: bool = True
    eligibility_reason: Optional[str] = None

class StationInfo(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    zone_type: str
    current_pm25: float
    current_aqi: Optional[float]
    category: str
    color: str
    dominant_pollutant: Optional[str] = None
    last_updated: Optional[str] = None
    freshness: str = "fresh"
    age_seconds: Optional[float] = None
    data_status: str = "observed"

class PredictionPoint(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    latitude: float
    longitude: float
    target: str = "PM2.5"
    unit: str = "µg/m³"
    predicted_pm25: float
    derived_pm25_sub_index: Optional[float] = None
    predicted_aqi: Optional[float] = None
    category: str
    color: str
    lower_bound_pm25: float
    upper_bound_pm25: float
    disagreement_range_lower: float
    disagreement_range_upper: float
    ensemble_std: float = 0.0
    confidence_level: str = "Ensemble Prediction Spread (Inter-Model Disagreement Range)"
    uncertainty_label: str = "Ensemble Prediction Spread (Inter-Model Disagreement Range)"
    empirical_coverage_pct: Optional[float] = None
    issued_at: str
    valid_at: str
    horizon: str = "+24h"
    model_version: str = "Chennai-AQI-Stacking-v2.2"
    uncertainty_status: str = "ensemble_spread"
    input_status: str = "fallback_demo_inputs"
    weather_vintage_status: str = "simulated_climatology"
    aqi_caveat: str = "Forecast is a PM2.5 concentration and its derived sub-index. Official CPCB AQI mandates 24h averaging across at least 3 pollutants with one particulate."
    data_status: str = "forecast"

class SpatialGridResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    grid: List[PredictionPoint]
    total_cells: int
    bounds: Dict[str, float]
    issued_at: str
    valid_at: str
    horizon: str = "+24h"
    model_version: str = "Chennai-AQI-Stacking-v2.2"
    target: str = "PM2.5"
    unit: str = "µg/m³"
    input_status: str = "fallback_demo_inputs"
    weather_vintage_status: str = "simulated_climatology"

class HotspotInfo(BaseModel):
    cluster_id: int
    center_latitude: float
    center_longitude: float
    mean_pm25: float
    estimated_aqi: float
    category: str
    color: str
    point_count: int
    severity: str
    method: str = "DBSCAN Spatial Density Clustering (eps=0.035, min_samples=3)"
    layer_type: str = "forecast"
    source_time_range: Optional[Dict[str, str]] = None
    spatial_reference: str = "EPSG:4326"
    data_mode: str = "demo"

class DataSourceInfo(BaseModel):
    name: str
    type: str
    provider: str
    description: str
    variables: List[str]
    access_method: str
    status: str
    mode: str = "demo"
    freshness: str = "fresh"
    attribution: str = ""

class ModelPerformanceItem(BaseModel):
    model: str
    mae: float
    rmse: float
    r2: float
    mape: float

class ModelPerformanceResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    best_model: str
    best_r2: float
    best_rmse: float
    best_mae: float
    comparison: List[ModelPerformanceItem]
    ensemble_weights: Dict[str, float]
    metadata: Dict[str, Any]
    model_card: Optional[Dict[str, Any]] = None

class FeatureContribution(BaseModel):
    feature: str
    name: str
    impact: float
    raw_value: float

class LocalExplanationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    base_value: float
    prediction_pm25: float
    target: str = "PM2.5"
    unit: str = "µg/m³"
    model_version: str = "Chennai-AQI-Stacking-v2.2"
    surrogate_model: str = "XGBoost Component of Stacking Ensemble"
    positive_contributors: List[FeatureContribution]
    negative_contributors: List[FeatureContribution]
    narrative: str
    disclaimer: str = "Feature attributions reflect statistical model associations, not direct physical causality."

class LocalityItem(BaseModel):
    name: str
    canonical_name: str
    latitude: float
    longitude: float
    zone: str
    type: str
    has_ground_station: bool
    station_id: Optional[str] = None
