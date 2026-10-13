"""
Official CPCB (Central Pollution Control Board, India) Air Quality Index Breakpoints.
Reference Document: Central Pollution Control Board (CPCB), Ministry of Environment,
Forest & Climate Change, Government of India: 'National Air Quality Index' Technical Report (2014-2015).
Doc URLs:
- https://airquality.cpcb.gov.in/ccr_docs/FINAL-REPORT_AQI_.pdf
- https://www.cpcb.gov.in/displaypdf.php?id=bmF0aW9uYWwtYWlyLXF1YWxpdHktaW5kZXgvRklOQUwtUkVQT1JUX0FRSV8ucGRm

Sub-index calculation formula:
    I_p = ((I_Hi - I_Lo) / (B_Hi - B_Lo)) * (C_p - B_Lo) + I_Lo

CPCB Categories:
    0 - 50: Good
    51 - 100: Satisfactory
    101 - 200: Moderate
    201 - 300: Poor
    301 - 400: Very Poor
    401 - 500: Severe
"""

from typing import Dict, List, Tuple

CPCB_METHOD_VERSION = "CPCB-NAQI-2014-v1.0"

# Official CPCB Sub-index Breakpoints: (B_Lo, B_Hi, I_Lo, I_Hi)
# All concentrations in µg/m³ except CO (mg/m³)
CPCB_BREAKPOINTS: Dict[str, List[Tuple[float, float, float, float]]] = {
    "PM2.5": [
        (0.0, 30.0, 0.0, 50.0),
        (30.1, 60.0, 51.0, 100.0),
        (60.1, 90.0, 101.0, 200.0),
        (90.1, 120.0, 201.0, 300.0),
        (120.1, 250.0, 301.0, 400.0),
        (250.1, 500.0, 401.0, 500.0),
    ],
    "PM10": [
        (0.0, 50.0, 0.0, 50.0),
        (50.1, 100.0, 51.0, 100.0),
        (100.1, 250.0, 101.0, 200.0),
        (250.1, 350.0, 201.0, 300.0),
        (350.1, 430.0, 301.0, 400.0),
        (430.1, 600.0, 401.0, 500.0),
    ],
    "NO2": [
        (0.0, 40.0, 0.0, 50.0),
        (40.1, 80.0, 51.0, 100.0),
        (80.1, 180.0, 101.0, 200.0),
        (180.1, 280.0, 201.0, 300.0),
        (280.1, 400.0, 301.0, 400.0),
        (400.1, 800.0, 401.0, 500.0),
    ],
    "SO2": [
        (0.0, 40.0, 0.0, 50.0),
        (40.1, 80.0, 51.0, 100.0),
        (80.1, 380.0, 101.0, 200.0),
        (380.1, 800.0, 201.0, 300.0),
        (800.1, 1600.0, 301.0, 400.0),
        (1600.1, 2400.0, 401.0, 500.0),
    ],
    "CO": [
        (0.0, 1.0, 0.0, 50.0),
        (1.01, 2.0, 51.0, 100.0),
        (2.01, 10.0, 101.0, 200.0),
        (10.01, 17.0, 201.0, 300.0),
        (17.01, 34.0, 301.0, 400.0),
        (34.01, 50.0, 401.0, 500.0),
    ],
    "O3": [
        (0.0, 50.0, 0.0, 50.0),
        (50.1, 100.0, 51.0, 100.0),
        (100.1, 168.0, 101.0, 200.0),
        (168.1, 208.0, 201.0, 300.0),
        (208.1, 748.0, 301.0, 400.0),
        (748.1, 1000.0, 401.0, 500.0),
    ],
    "NH3": [
        (0.0, 200.0, 0.0, 50.0),
        (200.1, 400.0, 51.0, 100.0),
        (400.1, 800.0, 101.0, 200.0),
        (800.1, 1200.0, 201.0, 300.0),
        (1200.1, 1800.0, 301.0, 400.0),
        (1800.1, 2400.0, 401.0, 500.0),
    ],
    "PB": [
        (0.0, 0.5, 0.0, 50.0),
        (0.51, 1.0, 51.0, 100.0),
        (1.01, 2.0, 101.0, 200.0),
        (2.01, 3.0, 201.0, 300.0),
        (3.01, 3.5, 301.0, 400.0),
        (3.51, 5.0, 401.0, 500.0),
    ]
}

# Averaging windows per pollutant under CPCB standard
POLLUTANT_AVERAGING_PERIODS: Dict[str, str] = {
    "PM2.5": "24h",
    "PM10": "24h",
    "NO2": "24h",
    "SO2": "24h",
    "CO": "8h",
    "O3": "8h",
    "NH3": "24h",
    "PB": "24h"
}

# Standard units per pollutant under CPCB
POLLUTANT_UNITS: Dict[str, str] = {
    "PM2.5": "µg/m³",
    "PM10": "µg/m³",
    "NO2": "µg/m³",
    "SO2": "µg/m³",
    "CO": "mg/m³",
    "O3": "µg/m³",
    "NH3": "µg/m³",
    "PB": "µg/m³"
}

AQI_CATEGORIES = [
    (0, 50, "Good", "#10B981", "Minimal impact. Air quality is considered satisfactory, and air pollution poses little or no risk."),
    (51, 100, "Satisfactory", "#84CC16", "Minor breathing discomfort to sensitive people."),
    (101, 200, "Moderate", "#F59E0B", "Breathing discomfort to people with lungs, asthma and heart diseases."),
    (201, 300, "Poor", "#EF4444", "Breathing discomfort to most people on prolonged exposure."),
    (301, 400, "Very Poor", "#9333EA", "Respiratory illness on prolonged exposure."),
    (401, 500, "Severe", "#7F1D1D", "Affects healthy people and seriously impacts those with existing diseases. Emergency health warning.")
]
