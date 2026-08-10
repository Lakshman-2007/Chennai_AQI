"""
region.py

Defines the Chennai geographic region as an ee.Geometry, per PRD section 4.

Supports:
  - "bbox": a simple bounding box (MVP default — simple but includes area
    outside the actual Chennai administrative boundary).
  - "boundary": a proper administrative polygon, loaded from a GeoJSON file
    (preferred for production use).

The chosen method and its exact coordinates/source are always returned
alongside the geometry so they can be written into the run metadata
(PRD section 11, "region_definition" must be recorded).
"""

from __future__ import annotations

import json
from typing import Any

from config import RegionConfig


def build_region(region_cfg: RegionConfig) -> tuple[Any, dict[str, Any]]:
    """Build an ee.Geometry for the configured region.

    Returns:
        (geometry, region_definition) where region_definition is a JSON-
        serializable dict describing exactly how the geometry was built,
        for the metadata file.
    """
    import ee

    if region_cfg.method == "bbox":
        geometry = ee.Geometry.BBox(
            region_cfg.min_lon,
            region_cfg.min_lat,
            region_cfg.max_lon,
            region_cfg.max_lat,
        )
        definition = {
            "method": "bbox",
            "min_lat": region_cfg.min_lat,
            "max_lat": region_cfg.max_lat,
            "min_lon": region_cfg.min_lon,
            "max_lon": region_cfg.max_lon,
            "note": (
                "Bounding box — includes area outside the actual Chennai "
                "administrative boundary. Use method='boundary' for a "
                "production-accurate region."
            ),
        }
        return geometry, definition

    if region_cfg.method == "boundary":
        if not region_cfg.boundary_source:
            raise ValueError(
                "region.method is 'boundary' but region.boundary_source "
                "(path to a GeoJSON polygon) was not provided."
            )
        with open(region_cfg.boundary_source, "r") as f:
            geojson = json.load(f)

        # Accept either a bare geometry, a Feature, or a FeatureCollection.
        if geojson.get("type") == "FeatureCollection":
            coords_geom = geojson["features"][0]["geometry"]
        elif geojson.get("type") == "Feature":
            coords_geom = geojson["geometry"]
        else:
            coords_geom = geojson

        geometry = ee.Geometry(coords_geom)
        definition = {
            "method": "boundary",
            "boundary_source": region_cfg.boundary_source,
        }
        return geometry, definition

    raise ValueError(
        f"Unknown region.method '{region_cfg.method}'. Use 'bbox' or 'boundary'."
    )
