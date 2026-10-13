import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml.model_registry import ModelRegistry

client = TestClient(app)

def test_prediction_point_endpoint():
    registry = ModelRegistry.get_instance()
    registry.reset_for_test()

    # 1. Valid request + ready model returns documented success status and finite prediction
    payload = {"latitude": 13.0827, "longitude": 80.2707, "horizon": "+24h"}
    response = client.post("/api/predictions/point", json=payload)
    assert response.status_code == 200
    pt = response.json()
    assert pt["target"] == "PM2.5"
    assert pt["unit"] == "µg/m³"
    assert pt["horizon"] == "+24h"
    assert pt["derived_pm25_sub_index"] is not None
    assert pt["disagreement_range_lower"] <= pt["predicted_pm25"] <= pt["disagreement_range_upper"]
    assert "Ensemble Prediction Spread" in pt["confidence_level"]
    assert pt["input_status"] == "fallback_demo_inputs"
    assert pt["weather_vintage_status"] == "simulated_climatology"
    assert pt["valid_at"] > pt["issued_at"]

    # 2. Invalid horizon returns 422
    bad_horizon = client.post("/api/predictions/point", json={"latitude": 13.0827, "longitude": 80.2707, "horizon": "+3h"})
    assert bad_horizon.status_code == 422

    # 3. Malformed / out of bounds coordinates returns 422
    bad_coords = client.post("/api/predictions/point", json={"latitude": 45.0, "longitude": 80.2707, "horizon": "+24h"})
    assert bad_coords.status_code == 422

    # 4. Unavailable model returns controlled 503
    try:
        registry.set_unready_for_test(core=True)
        res_503 = client.post("/api/predictions/point", json=payload)
        assert res_503.status_code == 503
        data_503 = res_503.json()
        assert data_503["code"] == "MODEL_NOT_READY"
        assert "error" in data_503
    finally:
        registry.reset_for_test()
