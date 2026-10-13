"""
Official CPCB NAQI Verification Test Suite.
Tests breakpoints, boundary values, official CPCB examples, eligibility rules, and edge cases.
"""

import pytest
import math
from backend.app.aqi.calculator import (
    calculate_pollutant_sub_index,
    get_aqi_category,
    calculate_cpcb_aqi,
    check_averaging_completeness
)
from backend.app.aqi.breakpoints import CPCB_METHOD_VERSION

class TestCPCBSubIndexCalculation:
    """Tests linear sub-index interpolation across all CPCB breakpoints."""

    def test_pm25_breakpoints_boundaries(self):
        # 0 - 30 -> 0 - 50
        assert calculate_pollutant_sub_index("PM2.5", 0.0) == 0.0
        assert calculate_pollutant_sub_index("PM2.5", 15.0) == pytest.approx(25.0, abs=0.5)
        assert calculate_pollutant_sub_index("PM2.5", 30.0) == pytest.approx(50.0, abs=0.5)

        # 30.1 - 60 -> 51 - 100
        assert calculate_pollutant_sub_index("PM2.5", 30.1) == pytest.approx(51.0, abs=0.5)
        assert calculate_pollutant_sub_index("PM2.5", 45.0) == pytest.approx(75.5, abs=1.0)
        assert calculate_pollutant_sub_index("PM2.5", 60.0) == pytest.approx(100.0, abs=0.5)

        # 60.1 - 90 -> 101 - 200
        assert calculate_pollutant_sub_index("PM2.5", 60.1) == pytest.approx(101.0, abs=0.5)
        assert calculate_pollutant_sub_index("PM2.5", 75.0) == pytest.approx(150.0, abs=1.0)
        assert calculate_pollutant_sub_index("PM2.5", 90.0) == pytest.approx(200.0, abs=0.5)

        # 90.1 - 120 -> 201 - 300
        assert calculate_pollutant_sub_index("PM2.5", 90.1) == pytest.approx(201.0, abs=0.5)
        assert calculate_pollutant_sub_index("PM2.5", 105.0) == pytest.approx(250.0, abs=1.0)
        assert calculate_pollutant_sub_index("PM2.5", 120.0) == pytest.approx(300.0, abs=0.5)

        # 120.1 - 250 -> 301 - 400
        assert calculate_pollutant_sub_index("PM2.5", 120.1) == pytest.approx(301.0, abs=0.5)
        assert calculate_pollutant_sub_index("PM2.5", 250.0) == pytest.approx(400.0, abs=0.5)

        # 250.1 - 500 -> 401 - 500
        assert calculate_pollutant_sub_index("PM2.5", 250.1) == pytest.approx(401.0, abs=0.5)
        assert calculate_pollutant_sub_index("PM2.5", 500.0) == pytest.approx(500.0, abs=0.5)

    def test_pm10_breakpoints_boundaries(self):
        assert calculate_pollutant_sub_index("PM10", 0.0) == 0.0
        assert calculate_pollutant_sub_index("PM10", 50.0) == pytest.approx(50.0, abs=0.5)
        assert calculate_pollutant_sub_index("PM10", 100.0) == pytest.approx(100.0, abs=0.5)
        assert calculate_pollutant_sub_index("PM10", 250.0) == pytest.approx(200.0, abs=0.5)
        assert calculate_pollutant_sub_index("PM10", 350.0) == pytest.approx(300.0, abs=0.5)
        assert calculate_pollutant_sub_index("PM10", 430.0) == pytest.approx(400.0, abs=0.5)
        assert calculate_pollutant_sub_index("PM10", 600.0) == pytest.approx(500.0, abs=0.5)

    def test_gaseous_pollutants(self):
        # NO2: 0-40 -> 0-50, 40.1-80 -> 51-100
        assert calculate_pollutant_sub_index("NO2", 40.0) == pytest.approx(50.0, abs=0.5)
        assert calculate_pollutant_sub_index("NO2", 80.0) == pytest.approx(100.0, abs=0.5)

        # SO2: 0-40 -> 0-50, 40.1-80 -> 51-100, 80.1-380 -> 101-200
        assert calculate_pollutant_sub_index("SO2", 40.0) == pytest.approx(50.0, abs=0.5)
        assert calculate_pollutant_sub_index("SO2", 80.0) == pytest.approx(100.0, abs=0.5)

        # CO (mg/m³): 0-1.0 -> 0-50, 1.01-2.0 -> 51-100
        assert calculate_pollutant_sub_index("CO", 1.0) == pytest.approx(50.0, abs=0.5)
        assert calculate_pollutant_sub_index("CO", 2.0) == pytest.approx(100.0, abs=0.5)

        # O3: 0-50 -> 0-50, 50.1-100 -> 51-100
        assert calculate_pollutant_sub_index("O3", 50.0) == pytest.approx(50.0, abs=0.5)
        assert calculate_pollutant_sub_index("O3", 100.0) == pytest.approx(100.0, abs=0.5)

        # NH3: 0-200 -> 0-50, 200.1-400 -> 51-100
        assert calculate_pollutant_sub_index("NH3", 200.0) == pytest.approx(50.0, abs=0.5)
        assert calculate_pollutant_sub_index("NH3", 400.0) == pytest.approx(100.0, abs=0.5)

        # PB: 0-0.5 -> 0-50
        assert calculate_pollutant_sub_index("PB", 0.5) == pytest.approx(50.0, abs=0.5)

    def test_invalid_and_extreme_inputs(self):
        # Negative concentration
        assert calculate_pollutant_sub_index("PM2.5", -5.0) is None
        # None concentration
        assert calculate_pollutant_sub_index("PM2.5", None) is None
        # Unknown pollutant
        assert calculate_pollutant_sub_index("UNKNOWN_GAS", 50.0) is None
        # Over maximum breakpoint (e.g. PM2.5 > 500)
        res_over = calculate_pollutant_sub_index("PM2.5", 700.0)
        assert res_over == 500.0

class TestCPCBEligibilityAndAggregation:
    """Tests the mandatory CPCB rules: >=3 pollutants, >=1 particulate matter."""

    def test_eligible_aqi_calculation(self):
        pollutants = {
            "PM2.5": 75.0,  # sub-index ~ 150 (Moderate)
            "PM10": 120.0,  # sub-index ~ 114 (Moderate)
            "NO2": 35.0,    # sub-index ~ 44 (Good)
            "SO2": 25.0     # sub-index ~ 31 (Good)
        }
        res = calculate_cpcb_aqi(pollutants, strict_eligibility=True)
        assert res["eligible"] is True
        assert res["aqi"] == 150
        assert res["dominant_pollutant"] == "PM2.5"
        assert res["category"] == "Moderate"
        assert res["method_version"] == CPCB_METHOD_VERSION

    def test_ineligible_fewer_than_three_pollutants(self):
        # Only 2 pollutants
        pollutants = {
            "PM2.5": 75.0,
            "NO2": 35.0
        }
        res = calculate_cpcb_aqi(pollutants, strict_eligibility=True)
        assert res["eligible"] is False
        assert res["aqi"] is None
        assert res["category"] == "Insufficient Data"
        assert "Insufficient pollutant count" in res["eligibility_reason"]

    def test_ineligible_no_particulate_matter(self):
        # 3 pollutants, but all gaseous (NO2, SO2, CO) - missing PM2.5/PM10
        pollutants = {
            "NO2": 45.0,
            "SO2": 25.0,
            "CO": 1.2
        }
        res = calculate_cpcb_aqi(pollutants, strict_eligibility=True)
        assert res["eligible"] is False
        assert res["aqi"] is None
        assert res["category"] == "Insufficient Data"
        assert "Missing mandatory particulate matter observation" in res["eligibility_reason"]

    def test_dominant_pollutant_tie_breaking(self):
        # Tie between PM2.5 and PM10
        pollutants = {
            "PM2.5": 30.0,  # sub-index = 50.0
            "PM10": 50.0,   # sub-index = 50.0
            "NO2": 20.0     # sub-index = 25.0
        }
        res = calculate_cpcb_aqi(pollutants, strict_eligibility=True)
        assert res["eligible"] is True
        assert res["aqi"] == 50
        # Priority order gives PM2.5 precedence in tie
        assert res["dominant_pollutant"] == "PM2.5"

class TestAveragingCompleteness:
    """Tests 24h (>=16h) and 8h (>=6h) averaging data completeness."""

    def test_24h_averaging(self):
        eligible, pct, period = check_averaging_completeness("PM2.5", valid_hours=16, total_hours=24)
        assert eligible is True
        assert pct >= 66.6
        assert period == "24h"

        eligible_fail, pct_fail, _ = check_averaging_completeness("PM2.5", valid_hours=15, total_hours=24)
        assert eligible_fail is False

    def test_8h_averaging(self):
        eligible, pct, period = check_averaging_completeness("CO", valid_hours=6, total_hours=8)
        assert eligible is True
        assert pct == 75.0
        assert period == "8h"

        eligible_fail, _, _ = check_averaging_completeness("CO", valid_hours=5, total_hours=8)
        assert eligible_fail is False
