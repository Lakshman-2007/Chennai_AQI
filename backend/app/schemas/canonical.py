"""
Canonical Observation and Data Ingestion Schemas.
Enforces Section 5.3 and 21.1/21.5 of the Chennai_AQI PRD.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class DataStatusEnum(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    ESTIMATED = "estimated"
    FORECAST = "forecast"
    SYNTHETIC = "synthetic"
    MANUAL_IMPORT = "manual_import"

class QualityFlagEnum(str, Enum):
    VALID = "valid"
    SUSPECT = "suspect"
    REJECTED = "rejected"
    CALIBRATED = "calibrated"

class DataSourceMode(str, Enum):
    DEMO = "demo"
    MANUAL_IMPORT = "manual_import"
    LIVE = "live"

class FreshnessStatus(str, Enum):
    FRESH = "fresh"         # age <= 2h
    STALE = "stale"         # 2h < age <= 24h
    EXPIRED = "expired"     # age > 24h
    UNAVAILABLE = "unavailable"

class CanonicalObservation(BaseModel):
    record_id: str = Field(description="Unique normalized record UUID/ID")
    source_id: str = Field(description="Identifier of originating provider or adapter")
    source_record_id: Optional[str] = Field(default=None, description="Raw source record identifier")
    station_id: Optional[str] = Field(default=None, description="Authoritative ground monitoring station ID")
    station_name: Optional[str] = Field(default=None, description="Monitoring station name")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    observed_at: datetime = Field(description="Timezone-aware timestamp of actual observation")
    retrieved_at: datetime = Field(description="Timezone-aware timestamp when ingested")
    pollutant: str = Field(description="Normalized pollutant code: PM2.5, PM10, NO2, SO2, CO, O3, NH3, PB")
    value: Optional[float] = Field(default=None, description="Measured numeric value or None for missing")
    unit: str = Field(description="Standard unit: µg/m³ or mg/m³")
    averaging_period: str = Field(default="1h", description="Averaging period: 1h, 8h, 24h")
    quality_flag: QualityFlagEnum = Field(default=QualityFlagEnum.VALID)
    data_status: DataStatusEnum = Field(default=DataStatusEnum.OBSERVED)
    raw_payload_ref: Optional[str] = Field(default=None, description="Raw file path or SHA-256 digest")

class ImportManifest(BaseModel):
    import_id: str
    source_file: str
    file_sha256: str
    source_url_or_origin: str
    downloaded_at: datetime
    imported_at: datetime
    total_rows_read: int
    rows_accepted: int
    rows_rejected: int
    rejection_reasons: Dict[str, int]
    station_ids_found: List[str]
    pollutants_found: List[str]
    time_range_start: Optional[str]
    time_range_end: Optional[str]
    status: str

class SourceHealthStatus(BaseModel):
    source_id: str
    name: str
    provider: str
    mode: DataSourceMode
    status: str  # healthy, degraded, unavailable
    last_attempt_at: Optional[datetime]
    last_success_at: Optional[datetime]
    age_seconds: Optional[float]
    freshness: FreshnessStatus
    stale_threshold_hours: float
    record_count: int
    data_status: DataStatusEnum
    error_message: Optional[str] = None
    attribution: str
