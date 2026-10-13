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

from backend.app.exceptions import ModelNotReadyException, model_not_ready_exception_handler

app = FastAPI(
    title="Chennai Air Quality Intelligence System",
    description="Hybrid Explainable Multi-Source Air Quality Prediction Framework for Chennai using Sentinel-5P Satellite Data, Ground Stations, Weather Data, and Walk-Forward Stacking ML.",
    version="2.2.0"
)

# Exception handlers (PRD v2.2 C-01 & C-10)
app.add_exception_handler(ModelNotReadyException, model_not_ready_exception_handler)

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
    Comprehensive system health, liveness, and readiness check (FR-22 & PRD v2.2 C-10).
    Separates process liveness, data readiness, and model registry readiness.
    """
    store = DataStore.get_instance()
    registry = ModelRegistry.get_instance()
    mode = store.get_mode().value

    model_status = registry.get_status()
    data_ready = store._df is not None and not store._df.empty
    model_ready = registry.is_ready

    return {
        "status": "healthy" if (model_ready and data_ready) else ("ready" if model_ready else "degraded"),
        "app_alive": True,
        "model_ready": model_ready,
        "data_ready": data_ready,
        "system": "Chennai AQI Intelligence Platform",
        "version": "2.2.0",
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
