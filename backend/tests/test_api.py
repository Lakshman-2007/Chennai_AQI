"""
FastAPI Integration & API Contract Verification Test Suite.
Fully satisfies PRD v2.3 Acceptance Requirements for all six endpoints:
- test_health_endpoint
- test_prediction_map_endpoint
- test_prediction_point_endpoint
- test_hotspots_endpoint
- test_global_explain_endpoint
- test_point_explain_endpoint
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml.model_registry import ModelRegistry

client = TestClient(app)

# --------------------------------------------------------------------------
# 4.1 test_health_endpoint
# --------------------------------------------------------------------------
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
    assert data["explainer_ready"] is True
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

# --------------------------------------------------------------------------
# 4.2 test_prediction_point_endpoint
# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
# 4.3 test_prediction_map_endpoint
# --------------------------------------------------------------------------
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
    # Ensure all cells are finite
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

# --------------------------------------------------------------------------
# 4.4 test_hotspots_endpoint
# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
# 4.5 test_global_explain_endpoint
# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
# 4.6 test_point_explain_endpoint
# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
# Other General API Routes
# --------------------------------------------------------------------------
def test_overview_endpoint():
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    assert "current_aqi" in data
    assert "category" in data
    assert "pollutants" in data
    assert "data_mode" in data
    assert "freshness" in data

def test_stations_endpoint():
    response = client.get("/api/stations")
    assert response.status_code == 200
    stations = response.json()
    assert isinstance(stations, list)
    assert len(stations) > 0
    assert "Alandur Bus Depot" in [s["name"] for s in stations]

def test_station_detail_endpoint():
    response = client.get("/api/stations/station_01")
    assert response.status_code == 200
    st = response.json()
    assert st["id"] == "station_01"
    assert "pollutant_readings" in st

def test_model_performance_endpoint():
    response = client.get("/api/model/performance")
    assert response.status_code == 200
    data = response.json()
    assert "best_r2" in data
    assert len(data["comparison"]) >= 9
    assert "model_card" in data

def test_data_sources_endpoints():
    response = client.get("/api/data/sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 3

    resp_status = client.get("/api/data/status")
    assert resp_status.status_code == 200
    assert "sources" in resp_status.json()

    resp_quality = client.get("/api/data/quality")
    assert resp_quality.status_code == 200
    assert resp_quality.json()["scientific_integrity_verified"] is True

def test_gis_endpoints():
    res = client.get("/api/localities?q=Alandur")
    assert res.status_code == 200
    locs = res.json()
    assert len(locs) > 0
    assert "Alandur" in locs[0]["canonical_name"]

    res_geo = client.get("/api/boundaries/wards")
    assert res_geo.status_code == 200
    geo = res_geo.json()
    assert geo["type"] == "FeatureCollection"
    assert len(geo["features"]) == 15

def test_export_endpoint():
    res_csv = client.get("/api/export?format=csv&days=7")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "timestamp,station_id" in res_csv.text

    res_json = client.get("/api/export?format=json&days=7")
    assert res_json.status_code == 200
    data = res_json.json()
    assert "metadata" in data
    assert "records" in data
