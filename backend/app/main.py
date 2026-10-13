"""
FastAPI Main Application Entrypoint for Chennai Air Quality Framework.
Version 2.1.0 — Binding Engineering Amendments & Operational Release Gates.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import (
    air_quality,
    stations,
    predictions,
    hotspots,
    explain,
    model_info,
    data_sources,
    gis
)
from backend.app.ml.model_registry import ModelRegistry
from backend.app.data_processing.store import DataStore

app = FastAPI(
    title="Chennai Air Quality Intelligence System",
    description="Hybrid Explainable Multi-Source Air Quality Prediction Framework for Chennai using Sentinel-5P Satellite Data, Ground Stations, Weather Data, and Walk-Forward Stacking ML.",
    version="2.1.0"
)

# CORS Middleware (allows React frontend connection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(air_quality.router)
app.include_router(stations.router)
app.include_router(predictions.router)
app.include_router(hotspots.router)
app.include_router(explain.router)
app.include_router(model_info.router)
app.include_router(data_sources.router)
app.include_router(gis.router)

@app.get("/api/health", tags=["Health"])
def health_check():
    """
    Comprehensive system health and readiness check (FR-22).
    Evaluates application state, data store, and model registry readiness.
    """
    store = DataStore.get_instance()
    registry = ModelRegistry.get_instance()
    mode = store.get_mode().value

    model_status = registry.get_status()
    all_ready = registry.is_ready and (store._df is not None and not store._df.empty)

    return {
        "status": "healthy" if all_ready else "degraded",
        "system": "Chennai AQI Intelligence Platform",
        "version": "2.1.0",
        "city": "Chennai, Tamil Nadu, India",
        "data_mode": mode,
        "is_synthetic": mode == "demo",
        "model": model_status,
        "cpcb_eligibility_enforced": True,
        "crs": "EPSG:4326"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
