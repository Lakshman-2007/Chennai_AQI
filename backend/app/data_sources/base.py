"""
Abstract Base Class for Data Source Adapters.
Defines required interface for ground observations, weather, satellite, and GIS sources.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from backend.app.schemas.canonical import SourceHealthStatus

class BaseDataSourceAdapter(ABC):
    """
    Standard interface for all Chennai AQI data source adapters.
    Ensures provider-independence, traceability, schema normalization, and health checks.
    """

    @abstractmethod
    def get_source_id(self) -> str:
        """Returns unique identifier for this data source."""
        pass

    @abstractmethod
    def health_check(self) -> SourceHealthStatus:
        """Evaluates connectivity, freshness, and operational health."""
        pass

    @abstractmethod
    def fetch(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        area: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch raw payload from external provider or local ingest."""
        pass

    @abstractmethod
    def validate(self, payload: Any) -> Tuple[bool, List[str]]:
        """Validates payload schema, boundary constraints, and CRS coordinates."""
        pass

    @abstractmethod
    def normalize(self, payload: Any) -> List[Dict[str, Any]]:
        """Transforms validated payload into canonical observation schema."""
        pass
