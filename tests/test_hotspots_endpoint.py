import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml.model_registry import ModelRegistry

client = TestClient(app)

def test_hotspots_endpoint():
    registry = ModelRegistry.get_instance()
    registry.reset_for_test()

    # 1. Ready state returns forecast hotspots
    res = client.get("/api/hotspots?threshold_pm25=50.0")
    assert res.status_code == 200
    hotspots = res.json()
    assert isinstance(hotspots, list)
    if len(hotspots) > 0:
        h0 = hotspots[0]
        assert "layer_type" in h0
        assert h0["spatial_reference"] == "EPSG:4326"

    # 2. Data-derived hotspot request succeeds with valid fixture observations even if model is disabled
    try:
        registry.set_unready_for_test(core=True)
        res_obs = client.get("/api/hotspots?source=observed&threshold_pm25=40.0")
        assert res_obs.status_code == 200
        obs_hotspots = res_obs.json()
        assert isinstance(obs_hotspots, list)
        for h in obs_hotspots:
            assert h["layer_type"] == "observed"

        # 3. Forecast hotspot request returns 503 when model is unavailable
        res_fc_fail = client.get("/api/hotspots?source=forecast&threshold_pm25=50.0")
        assert res_fc_fail.status_code == 503
        assert res_fc_fail.json()["code"] == "MODEL_NOT_READY"
    finally:
        registry.reset_for_test()

    # 4. Insufficient data / extreme threshold returns explicit empty response without fabrication
    res_extreme = client.get("/api/hotspots?source=observed&threshold_pm25=150.0")
    assert res_extreme.status_code == 200
    assert res_extreme.json() == []
