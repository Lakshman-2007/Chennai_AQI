import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["city"] == "Chennai, Tamil Nadu, India"

def test_overview_endpoint():
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    assert "current_aqi" in data
    assert "category" in data
    assert "pollutants" in data

def test_stations_endpoint():
    response = client.get("/api/stations")
    assert response.status_code == 200
    stations = response.json()
    assert isinstance(stations, list)
    assert len(stations) > 0
    assert "Alandur Bus Depot" in [s["name"] for s in stations]

def test_prediction_map_endpoint():
    response = client.get("/api/predictions/map?resolution=15")
    assert response.status_code == 200
    data = response.json()
    assert "grid" in data
    assert len(data["grid"]) == 15 * 15

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

def test_point_explain_endpoint():
    response = client.post("/api/explain/point", json={"latitude": 13.0827, "longitude": 80.2707})
    assert response.status_code == 200
    data = response.json()
    assert "positive_contributors" in data
    assert "narrative" in data

def test_model_performance_endpoint():
    response = client.get("/api/model/performance")
    assert response.status_code == 200
    data = response.json()
    assert "best_r2" in data
    assert len(data["comparison"]) >= 8

def test_data_sources_endpoint():
    response = client.get("/api/data/sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 3
