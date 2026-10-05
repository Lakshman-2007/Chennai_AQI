"""
Model Performance & Architecture API Router.
"""

import os
import json
from fastapi import APIRouter, HTTPException
from backend.app.schemas.schemas import ModelPerformanceResponse

router = APIRouter(prefix="/api/model", tags=["Model Info"])

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))

@router.get("/performance", response_model=ModelPerformanceResponse)
def get_model_performance():
    """
    Get full benchmark evaluation comparison table across all candidate ML models and Stacking Ensemble.
    """
    perf_path = os.path.join(MODELS_DIR, "performance.json")
    meta_path = os.path.join(MODELS_DIR, "metadata.json")
    
    if not os.path.exists(perf_path) or not os.path.exists(meta_path):
        raise HTTPException(status_code=500, detail="Performance metadata missing.")
        
    with open(perf_path, "r") as f:
        comparison = json.load(f)
        
    with open(meta_path, "r") as f:
        metadata = json.load(f)
        
    ens_res = next((m for m in comparison if "Ensemble" in m["model"]), comparison[-1])
    
    return {
        "best_model": ens_res["model"],
        "best_r2": ens_res["r2"],
        "best_rmse": ens_res["rmse"],
        "best_mae": ens_res["mae"],
        "comparison": comparison,
        "ensemble_weights": metadata.get("ensemble_weights", {}),
        "metadata": metadata
    }
