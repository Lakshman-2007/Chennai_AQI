"""
FastAPI Main Application Entrypoint for Chennai Air Quality Framework.
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
    data_sources
)

app = FastAPI(
    title="Chennai Air Quality Intelligence System",
    description="Hybrid Explainable Multi-Source Air Quality Prediction Framework for Chennai using Sentinel-5P Satellite Data, Ground Stations, Weather Data, and Ensemble ML.",
    version="2.0.0"
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

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "system": "Chennai AQI Prediction Framework",
        "version": "2.0.0",
        "city": "Chennai, Tamil Nadu, India"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
