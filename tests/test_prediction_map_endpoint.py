import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml.model_registry import ModelRegistry

client = TestClient(app)

def test_prediction_map_endpoint():
    registry = ModelRegistry.get_instance()
    registry.reset_for_test()

    # 1. Valid map request + ready model returns schema-valid grid features
    response = client.get("/api/predictions/map?resolution=12&horizon=+24h")
    assert response.status_code == 200
    data = response.json()
    assert "grid" in data
    assert len(data["grid"]) == 12 * 12
    issued = datetime.fromisoformat(data["issued_at"])
    valid = datetime.fromisoformat(data["valid_at"])
    assert valid > issued
    assert data["target"] == "PM2.5"
    assert data["unit"] == "µg/m³"
    for cell in data["grid"]:
        assert isinstance(cell["predicted_pm25"], (int, float))
        assert cell["predicted_pm25"] > 0

    # 2. Invalid horizon returns 422
    res_bad = client.get("/api/predictions/map?horizon=+99h")
    assert res_bad.status_code == 422

    # 3. Model unavailable returns controlled 503
    try:
        registry.set_unready_for_test(core=True)
        res_503 = client.get("/api/predictions/map?resolution=12&horizon=+24h")
        assert res_503.status_code == 503
        assert res_503.json()["code"] == "MODEL_NOT_READY"
    finally:
        registry.reset_for_test()
