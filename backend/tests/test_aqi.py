import pytest
from backend.app.aqi.calculator import (
    calculate_pollutant_sub_index,
    get_aqi_category,
    calculate_cpcb_aqi
)

def test_pm25_sub_index():
    assert calculate_pollutant_sub_index("PM2.5", 15.0) == pytest.approx(25.0, abs=0.5)
    assert calculate_pollutant_sub_index("PM2.5", 45.0) == pytest.approx(75.5, abs=1.0)
    assert calculate_pollutant_sub_index("PM2.5", 75.0) == pytest.approx(150.0, abs=1.0)
    assert calculate_pollutant_sub_index("PM2.5", 105.0) == pytest.approx(250.0, abs=1.0)

def test_aqi_category():
    cat, col, _ = get_aqi_category(35)
    assert cat == "Good"
    assert col == "#10B981"

    cat, col, _ = get_aqi_category(125)
    assert cat == "Moderate"
    assert col == "#F59E0B"

    cat, col, _ = get_aqi_category(250)
    assert cat == "Poor"
    assert col == "#EF4444"

def test_overall_cpcb_aqi():
    pollutants = {
        "PM2.5": 75.0,
        "PM10": 120.0,
        "NO2": 45.0,
        "SO2": 20.0
    }
    res = calculate_cpcb_aqi(pollutants)
    assert res["aqi"] is not None
    assert res["dominant_pollutant"] == "PM2.5"
    assert res["category"] == "Moderate"
