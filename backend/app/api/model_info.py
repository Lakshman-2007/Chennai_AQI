"""
Model Performance & Architecture API Router.
"""

from fastapi import APIRouter, HTTPException
from backend.app.schemas.schemas import ModelPerformanceResponse
from backend.app.ml.model_registry import ModelRegistry

router = APIRouter(prefix="/api/model", tags=["Model Info"])

@router.get("/performance", response_model=ModelPerformanceResponse)
def get_model_performance():
    """
    Get full benchmark evaluation comparison table across all candidate ML models,
    Persistence / Seasonal Baselines, and Walk-Forward Stacking Ensemble.
    """
    registry = ModelRegistry.get_instance()
    comparison = registry.performance
    metadata = registry.metadata
    model_card = registry.model_card

    if not comparison:
        raise HTTPException(status_code=503, detail="Performance metadata missing.")

    ens_res = next((m for m in comparison if "Ensemble" in m["model"]), comparison[-1])

    return {
        "best_model": ens_res["model"],
        "best_r2": ens_res["r2"],
        "best_rmse": ens_res["rmse"],
        "best_mae": ens_res["mae"],
        "comparison": comparison,
        "ensemble_weights": metadata.get("ensemble_weights", {}),
        "metadata": metadata,
        "model_card": model_card
    }
