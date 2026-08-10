"""
config.py

Loads pipeline configuration from a YAML file and exposes it as a
single validated Config object. Also holds the registry of verified
Sentinel-5P collection/band/QA combinations so the rest of the code
never has to hard-code or guess these values (PRD sections 8, 15).

Only NO2 is verified and wired up as the MVP default. Other
pollutants are listed but marked unverified — do not use them until
someone has checked the collection/band/QA against the current GEE
Sentinel-5P catalog (PRD section 23).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Verified Sentinel-5P dataset registry
#
# Each entry records exactly what PRD section 8 requires: which QA variable
# is used, what threshold, and why. Thresholds below come from the official
# Earth Engine Sentinel-5P catalog pages (harpconvert QA filtering notes):
#   - AER_AI:                       qa_value > 0.80
#   - NO2 tropospheric column band: qa_value > 0.75 (product recommends a
#                                    stricter threshold for this band)
#   - All other products (except O3, SO2 which are ingested differently):
#                                    qa_value > 0.50
# ---------------------------------------------------------------------------
DATASET_REGISTRY: dict[str, dict[str, Any]] = {
    "NO2": {
        "collection_id": "COPERNICUS/S5P/OFFL/L3_NO2",
        "band": "tropospheric_NO2_column_number_density",
        "unit": "mol/m^2",
        "qa_band": "qa_value",
        "qa_threshold": 0.75,
        "qa_reason": (
            "Earth Engine Sentinel-5P NO2 catalog documentation recommends "
            "qa_value > 0.75 specifically for the tropospheric_NO2_column_"
            "number_density band (stricter than the 0.50 default used for "
            "most other S5P products)."
        ),
        "verified": True,
    },
    # The following are placeholders only. Per PRD section 23, do NOT use
    # until the collection id / band / QA threshold have been individually
    # verified against the live GEE catalog.
    "CO": {"verified": False},
    "SO2": {"verified": False},
    "O3": {"verified": False},
    "CH4": {"verified": False},
    "HCHO": {"verified": False},
    "AER_AI": {"verified": False},
}


@dataclass
class RegionConfig:
    name: str = "Chennai"
    method: str = "bbox"  # "bbox" or "boundary"
    min_lat: float = 12.83
    max_lat: float = 13.27
    min_lon: float = 80.03
    max_lon: float = 80.34
    boundary_source: str | None = None  # e.g. path to a GeoJSON, if method="boundary"


@dataclass
class DateConfig:
    start: str = "2025-01-01"
    end: str = "2025-01-31"

    def as_dates(self) -> tuple[dt.date, dt.date]:
        start = dt.date.fromisoformat(self.start)
        end = dt.date.fromisoformat(self.end)
        if end < start:
            raise ValueError(f"end_date {end} is before start_date {start}")
        return start, end


@dataclass
class ProcessingConfig:
    variable: str = "NO2"
    temporal_resolution: str = "daily"  # daily | weekly | monthly
    spatial_aggregation: str = "mean"  # mean | median | min | max


@dataclass
class QualityConfig:
    enabled: bool = True
    # If None, the registry's default threshold for the chosen variable is used.
    threshold_override: float | None = None


@dataclass
class OutputConfig:
    format: str = "csv"
    output_dir: str = "output"
    csv_filename: str = "sentinel5p_chennai.csv"
    metadata_filename: str = "sentinel5p_chennai_metadata.json"
    processing_version: str = "v0.1"


@dataclass
class Config:
    region: RegionConfig = field(default_factory=RegionConfig)
    date: DateConfig = field(default_factory=DateConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        with open(path, "r") as f:
            raw = yaml.safe_load(f) or {}

        return cls(
            region=RegionConfig(**raw.get("region", {})),
            date=DateConfig(**raw.get("date", {})),
            processing=ProcessingConfig(**raw.get("processing", {})),
            quality=QualityConfig(**raw.get("quality", {})),
            output=OutputConfig(**raw.get("output", {})),
        )

    def dataset_spec(self) -> dict[str, Any]:
        """Look up and validate the registry entry for the configured variable."""
        variable = self.processing.variable
        if variable not in DATASET_REGISTRY:
            raise ValueError(
                f"Unknown variable '{variable}'. Known keys: "
                f"{list(DATASET_REGISTRY)}"
            )
        spec = DATASET_REGISTRY[variable]
        if not spec.get("verified", False):
            raise ValueError(
                f"Variable '{variable}' is not yet verified against the live "
                "GEE Sentinel-5P catalog (see config.py DATASET_REGISTRY). "
                "Verify collection_id/band/qa_band/qa_threshold before use. "
                "'NO2' is the only variable wired up for the MVP."
            )
        return spec
