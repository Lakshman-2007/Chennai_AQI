"""
FastAPI Integration & API Contract Verification Test Suite.
Verifies all public routes, response schemas, and PRD contract guarantees.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.app.main import app

from backend.app.ml.model_registry import ModelRegistry

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "ready", "degraded"]
    assert data["app_alive"] is True
    assert data["model_ready"] is True
    assert data["data_ready"] is True
    assert data["city"] == "Chennai, Tamil Nadu, India"
    assert "model" in data
    assert data["model"]["smoke_test_passed"] is True
    assert data["crs"] == "EPSG:4326"

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

def test_prediction_map_endpoint():
    response = client.get("/api/predictions/map?resolution=12&horizon=+24h")
    assert response.status_code == 200
    data = response.json()
    assert "grid" in data
    assert len(data["grid"]) == 12 * 12
    # Verify temporal guarantee: valid_at > issued_at
    issued = datetime.fromisoformat(data["issued_at"])
    valid = datetime.fromisoformat(data["valid_at"])
    assert valid > issued

def test_prediction_point_endpoint():
    payload = {"latitude": 13.0827, "longitude": 80.2707, "horizon": "+24h"}
    response = client.post("/api/predictions/point", json=payload)
    assert response.status_code == 200
    pt = response.json()
    assert pt["target"] == "PM2.5"
    assert pt["unit"] == "µg/m³"
    assert pt["derived_pm25_sub_index"] is not None
    assert pt["lower_bound_pm25"] <= pt["predicted_pm25"] <= pt["upper_bound_pm25"]
    assert pt["disagreement_range_lower"] == pt["lower_bound_pm25"]
    assert pt["disagreement_range_upper"] == pt["upper_bound_pm25"]
    assert "Ensemble Prediction Spread" in pt["confidence_level"]
    assert pt["input_status"] == "fallback_demo_inputs"
    assert pt["weather_vintage_status"] == "simulated_climatology"
    assert pt["valid_at"] > pt["issued_at"]

def test_invalid_horizon_returns_422():
    # Invalid horizon query parameter on /api/predictions/map
    res_map = client.get("/api/predictions/map?horizon=+3h")
    assert res_map.status_code == 422

    # Invalid horizon payload on /api/predictions/point
    res_pt = client.post("/api/predictions/point", json={"latitude": 13.0827, "longitude": 80.2707, "horizon": "+99h"})
    assert res_pt.status_code == 422

def test_unready_model_returns_controlled_503():
    registry = ModelRegistry.get_instance()
    original_ready = registry.is_ready
    try:
        registry.is_ready = False
        res = client.post("/api/predictions/point", json={"latitude": 13.0827, "longitude": 80.2707, "horizon": "+24h"})
        assert res.status_code == 503
        data = res.json()
        assert data["code"] == "MODEL_NOT_READY"

        res_exp = client.post("/api/explain/point", json={"latitude": 13.0827, "longitude": 80.2707})
        assert res_exp.status_code == 503
        assert res_exp.json()["code"] == "MODEL_NOT_READY"
    finally:
        registry.is_ready = original_ready

def test_hotspots_endpoint():
    response = client.get("/api/hotspots?threshold_pm25=50.0")
    assert response.status_code == 200
    hotspots = response.json()
    assert isinstance(hotspots, list)

def test_global_explain_endpoint():
    response = client.get("/api/explain/global")
    assert response.status_code == 200
    data = response.json()
    assert "global_importance" in data
    assert len(data["global_importance"]) > 0

def test_point_explain_endpoint():
    response = client.post("/api/explain/point", json={"latitude": 13.0827, "longitude": 80.2707})
    assert response.status_code == 200
    data = response.json()
    assert "positive_contributors" in data
    assert "negative_contributors" in data
    assert data["surrogate_model"] == "XGBoost Component of Stacking Ensemble"
    assert "narrative" in data
    assert "disclaimer" in data
    # Test additive consistency: base_value + sum(contribs) == prediction_pm25
    total_attributions = sum(c["impact"] for c in data["positive_contributors"] + data["negative_contributors"])
    expected_pred = data["base_value"] + total_attributions
    # Within small rounding tolerance
    assert abs(expected_pred - data["prediction_pm25"]) < 0.1

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
    # Localities gazetteer search
    res = client.get("/api/localities?q=Alandur")
    assert res.status_code == 200
    locs = res.json()
    assert len(locs) > 0
    assert "Alandur" in locs[0]["canonical_name"]

    # GCC zones GeoJSON
    res_geo = client.get("/api/boundaries/wards")
    assert res_geo.status_code == 200
    geo = res_geo.json()
    assert geo["type"] == "FeatureCollection"
    assert len(geo["features"]) == 15

def test_export_endpoint():
    # CSV export
    res_csv = client.get("/api/export?format=csv&days=7")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "timestamp,station_id" in res_csv.text

    # JSON export
    res_json = client.get("/api/export?format=json&days=7")
    assert res_json.status_code == 200
    data = res_json.json()
    assert "metadata" in data
    assert "records" in data
