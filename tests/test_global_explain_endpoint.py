import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml.model_registry import ModelRegistry

client = TestClient(app)

def test_global_explain_endpoint():
    registry = ModelRegistry.get_instance()
    registry.reset_for_test()

    # 1. Compatible explainer returns finite schema-valid importances identifying surrogate model
    response = client.get("/api/explain/global")
    assert response.status_code == 200
    data = response.json()
    assert "global_importance" in data
    assert len(data["global_importance"]) > 0
    assert data["surrogate_model"] == "XGBoost Component of Stacking Ensemble"

    # 2. Explainer unready state returns 503 EXPLAINER_NOT_READY without disabling core predictions
    try:
        registry.set_unready_for_test(explainer=True)
        res_exp_503 = client.get("/api/explain/global")
        assert res_exp_503.status_code == 503
        assert res_exp_503.json()["code"] == "EXPLAINER_NOT_READY"

        # Core prediction still works independently!
        res_pred = client.post("/api/predictions/point", json={"latitude": 13.0827, "longitude": 80.2707, "horizon": "+24h"})
        assert res_pred.status_code == 200
    finally:
        registry.reset_for_test()
