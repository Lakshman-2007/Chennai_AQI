import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml.model_registry import ModelRegistry

client = TestClient(app)

def test_health_endpoint():
    registry = ModelRegistry.get_instance()
    registry.reset_for_test()

    # 1. Ready state: liveness and readiness return documented healthy statuses
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["app_alive"] is True
    assert data["liveness"] == "alive"
    assert data["readiness"] == "ready"
    assert data["model_ready"] is True
    assert data["data_ready"] is True
    assert data["readiness_code"] == "READY"
    assert data["crs"] == "EPSG:4326"

    # Liveness probe returns 200
    live_res = client.get("/api/health/live")
    assert live_res.status_code == 200
    assert live_res.json()["app_alive"] is True

    # 2. Failed model state: liveness remains available; readiness reports model_not_ready
    try:
        registry.set_unready_for_test(core=True)
        res_fail = client.get("/api/health")
        assert res_fail.status_code == 200
        fail_data = res_fail.json()
        assert fail_data["app_alive"] is True
        assert fail_data["liveness"] == "alive"
        assert fail_data["readiness"] == "model_not_ready"
        assert fail_data["model_ready"] is False
        assert fail_data["readiness_code"] == "MODEL_NOT_READY"
        assert fail_data["status"] == "degraded"
    finally:
        registry.reset_for_test()
