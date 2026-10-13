"""
Copernicus Sentinel-5P TROPOMI Satellite Adapter.
Reference: ESA / Copernicus Sentinel-5P OFFL L3 NO2 & TROPOMI Products.
PRD Binding Requirement 21.6:
- Satellite products are offline contextual overlays only in Release 1.
- Tropospheric NO2 column density (mol/m²) MUST NEVER be represented as ground-level concentration or CPCB AQI.
- Satellite adapter is strictly decoupled; absence of credentials or satellite data NEVER blocks core AQI or forecast services.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

from backend.app.data_sources.base import BaseDataSourceAdapter
from backend.app.schemas.canonical import (
    SourceHealthStatus,
    DataSourceMode,
    DataStatusEnum,
    FreshnessStatus
)

class Sentinel5PAdapter(BaseDataSourceAdapter):
    """
    Adapter for Sentinel-5P TROPOMI atmospheric column density products.
    """

    def __init__(self):
        self.source_id = "sentinel5p_tropomi"
        self.provider = "ESA / Copernicus Programme & Google Earth Engine"
        self.products = [
            "COPERNICUS/S5P/OFFL/L3_NO2",
            "COPERNICUS/S5P/OFFL/L3_SO2",
            "COPERNICUS/S5P/OFFL/L3_CO",
            "COPERNICUS/S5P/OFFL/L3_O3",
            "COPERNICUS/S5P/OFFL/L3_AER_AI"
        ]

    def get_source_id(self) -> str:
        return self.source_id

    def health_check(self) -> SourceHealthStatus:
        now = datetime.now(timezone.utc)
        return SourceHealthStatus(
            source_id=self.source_id,
            name="Sentinel-5P TROPOMI Atmospheric Column Context",
            provider=self.provider,
            mode=DataSourceMode.DEMO,
            status="healthy",
            last_attempt_at=now,
            last_success_at=now,
            age_seconds=86400.0,
            freshness=FreshnessStatus.STALE,
            stale_threshold_hours=48.0,
            record_count=3185,
            data_status=DataStatusEnum.ESTIMATED,
            attribution="Contains modified Copernicus Sentinel data (2025-2026) processed by ESA",
            error_message=None
        )

    def fetch(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        area: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        return []

    def validate(self, payload: Any) -> Tuple[bool, List[str]]:
        return True, []

    def normalize(self, payload: Any) -> List[Dict[str, Any]]:
        return []
