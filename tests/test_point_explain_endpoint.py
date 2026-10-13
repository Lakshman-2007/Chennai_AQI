import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml.model_registry import ModelRegistry

client = TestClient(app)

def test_point_explain_endpoint():
    registry = ModelRegistry.get_instance()
    registry.reset_for_test()

    # 1. Valid point returns finite contributions and identifies surrogate model
    response = client.post("/api/explain/point", json={"latitude": 13.0827, "longitude": 80.2707})
    assert response.status_code == 200
    data = response.json()
    assert "positive_contributors" in data
    assert "negative_contributors" in data
    assert data["surrogate_model"] == "XGBoost Component of Stacking Ensemble"
    assert "narrative" in data
    assert "disclaimer" in data

    # 2. Test strict additive consistency: E[f(x)] + sum(all_attributions) == prediction_pm25
    total_attributions = sum(c["impact"] for c in data["positive_contributors"] + data["negative_contributors"])
    expected_pred = data["base_value"] + total_attributions
    assert abs(expected_pred - data["prediction_pm25"]) < 0.1

    # 3. Explainer unready returns 503 EXPLAINER_NOT_READY
    try:
        registry.set_unready_for_test(explainer=True)
        res_503 = client.post("/api/explain/point", json={"latitude": 13.0827, "longitude": 80.2707})
        assert res_503.status_code == 503
        assert res_503.json()["code"] == "EXPLAINER_NOT_READY"
    finally:
        registry.reset_for_test()

    # 4. Malformed coordinates return 422
    res_bad = client.post("/api/explain/point", json={"latitude": 99.0, "longitude": 80.2707})
    assert res_bad.status_code == 422
