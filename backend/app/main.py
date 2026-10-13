"""
FastAPI Main Application Entrypoint for Chennai Air Quality Framework.
Version 2.3.0 — Six Failing Tests Fix Addendum & Decoupled Model Readiness.
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

from backend.app.exceptions import (
    ModelNotReadyException,
    model_not_ready_exception_handler,
    ExplainerNotReadyException,
    explainer_not_ready_exception_handler
)

app = FastAPI(
    title="Chennai Air Quality Intelligence System",
    description="Hybrid Explainable Multi-Source Air Quality Prediction Framework for Chennai using Sentinel-5P Satellite Data, Ground Stations, Weather Data, and Walk-Forward Stacking ML.",
    version="2.3.0"
)

# Exception handlers (PRD v2.3 Section 3 & 5)
app.add_exception_handler(ModelNotReadyException, model_not_ready_exception_handler)
app.add_exception_handler(ExplainerNotReadyException, explainer_not_ready_exception_handler)

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
    Comprehensive system health, liveness, and readiness check (FR-22 & PRD v2.3 Section 4.1).
    Explicitly separates process liveness from application and model readiness.
    """
    store = DataStore.get_instance()
    registry = ModelRegistry.get_instance()
    mode = store.get_mode().value

    model_status = registry.get_status()
    data_ready = store._df is not None and not store._df.empty
    model_ready = registry.core_model_ready
    explainer_ready = registry.explainer_ready

    # Overall system health: healthy if both data and models ready; degraded if alive but models unready
    overall_status = "healthy" if (model_ready and data_ready and explainer_ready) else (
        "ready" if (model_ready and data_ready) else "degraded"
    )

    return {
        "status": overall_status,
        "app_alive": True,
        "liveness": "alive",
        "readiness": "ready" if model_ready else "model_not_ready",
        "readiness_code": "READY" if model_ready else registry.safe_error_code,
        "model_ready": model_ready,
        "explainer_ready": explainer_ready,
        "data_ready": data_ready,
        "system": "Chennai AQI Intelligence Platform",
        "version": "2.3.0",
        "city": "Chennai, Tamil Nadu, India",
        "data_mode": mode,
        "is_synthetic": mode == "demo",
        "model": model_status,
        "cpcb_eligibility_enforced": True,
        "crs": "EPSG:4326"
    }

@app.get("/api/health/live", tags=["Health"])
def liveness_probe():
    """Process liveness probe: returns 200 as long as the web process is running."""
    return {"status": "alive", "app_alive": True}

@app.get("/api/health/ready", tags=["Health"])
def readiness_probe():
    """Readiness probe: reports readiness state of prediction model and data store."""
    registry = ModelRegistry.get_instance()
    store = DataStore.get_instance()
    ready = registry.core_model_ready and (store._df is not None and not store._df.empty)
    return {
        "status": "ready" if ready else "not_ready",
        "model_ready": registry.core_model_ready,
        "data_ready": store._df is not None and not store._df.empty,
        "readiness_code": "READY" if registry.core_model_ready else registry.safe_error_code
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
