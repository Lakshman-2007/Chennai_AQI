"""
export.py

Writes the final CSV (FR-10) matching the PRD section 10 schema, plus a
companion metadata JSON file (PRD section 11) so the dataset is
reproducible and auditable.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
from typing import Any

CSV_FIELDS = [
    "date",
    "region",
    "latitude",
    "longitude",
    "variable",
    "value",
    "unit",
    "valid_pixel_count",
    "aggregation",
    "dataset",
    "processing_version",
]


def write_csv(
    observations: list[dict[str, Any]],
    output_path: str,
    region_name: str,
    region_centroid: tuple[float, float],
    variable: str,
    unit: str,
    aggregation: str,
    dataset: str,
    processing_version: str,
) -> None:
    """Write daily observations to CSV in the PRD section 10 schema.

    Missing observations are written as an empty value field (interpreted
    as NULL on read), never as 0 (PRD section 9, Rule 4).
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    lat, lon = region_centroid

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for obs in observations:
            writer.writerow(
                {
                    "date": obs["date"],
                    "region": region_name,
                    "latitude": lat,
                    "longitude": lon,
                    "variable": variable,
                    "value": "" if obs["value"] is None else obs["value"],
                    "unit": unit,
                    "valid_pixel_count": obs["valid_pixel_count"],
                    "aggregation": aggregation,
                    "dataset": dataset,
                    "processing_version": processing_version,
                }
            )


def write_metadata(
    output_path: str,
    *,
    collection_id: str,
    band: str,
    unit: str,
    start_date: str,
    end_date: str,
    region_name: str,
    region_definition: dict[str, Any],
    aggregation_method: str,
    quality_enabled: bool,
    qa_band: str,
    qa_threshold: float,
    qa_reason: str,
    processing_version: str,
) -> None:
    """Write the companion metadata JSON (PRD section 11)."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    metadata = {
        "dataset": "SENTINEL-5P",
        "collection_id": collection_id,
        "variable": band,
        "band": band,
        "unit": unit,
        "start_date": start_date,
        "end_date": end_date,
        "region": region_name,
        "region_definition": region_definition,
        "aggregation_method": aggregation_method,
        "quality_filter": {
            "enabled": quality_enabled,
            "qa_band": qa_band,
            "qa_threshold": qa_threshold,
            "reason": qa_reason,
        },
        "processing_version": processing_version,
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
    }

    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
