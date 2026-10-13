"""
Chennai GIS & Localities API Router.
Provides searchable locality gazetteer and GCC ward boundary GeoJSON (EPSG:4326).
"""

from typing import List, Optional
from fastapi import APIRouter, Query
from backend.app.schemas.schemas import LocalityItem
from backend.app.data_sources.chennai_gis_adapter import (
    search_localities,
    get_gcc_zones_geojson
)

router = APIRouter(prefix="/api", tags=["GIS & Boundaries"])

@router.get("/localities", response_model=List[LocalityItem])
def get_localities(
    q: Optional[str] = Query(None, description="Search query for locality name or alias"),
    limit: int = Query(20, ge=1, le=50)
):
    """
    Search curated Chennai localities gazetteer for map search and navigation.
    """
    results = search_localities(query=q or "", limit=limit)
    return results

@router.get("/boundaries/wards")
def get_chennai_ward_boundaries():
    """
    Get Greater Chennai Corporation (GCC) administrative zones boundary GeoJSON (EPSG:4326).
    """
    geojson = get_gcc_zones_geojson()
    return geojson
