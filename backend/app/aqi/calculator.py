"""
Official CPCB Air Quality Index Calculator Module.

Implements the official Indian National Air Quality Index (NAQI) methodology:
- Sub-index linear interpolation across breakpoint intervals
- 24h and 8h averaging completeness evaluation
- Mandatory CPCB minimum pollutant eligibility check (>=3 pollutants, with >=1 PM2.5 or PM10)
- Dominant pollutant resolution and category classification
"""

import math
from typing import Dict, Optional, Tuple, Any, List
from backend.app.aqi.breakpoints import (
    CPCB_BREAKPOINTS,
    AQI_CATEGORIES,
    CPCB_METHOD_VERSION,
    POLLUTANT_AVERAGING_PERIODS,
    POLLUTANT_UNITS
)

# Deterministic priority for tie-breaking dominant pollutant
POLLUTANT_PRIORITY = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3", "NH3", "PB"]

def normalize_pollutant_name(pollutant: str) -> Optional[str]:
    """Normalize user input or database pollutant string to canonical CPCB key."""
    if not pollutant or not isinstance(pollutant, str):
        return None
    cleaned = pollutant.strip().upper().replace(".", "").replace("_", "")
    if cleaned in ["PM25", "PM2"]:
        return "PM2.5"
    if cleaned in ["PM10"]:
        return "PM10"
    if cleaned in ["NO2"]:
        return "NO2"
    if cleaned in ["SO2"]:
        return "SO2"
    if cleaned in ["CO"]:
        return "CO"
    if cleaned in ["O3", "OZONE"]:
        return "O3"
    if cleaned in ["NH3", "AMMONIA"]:
        return "NH3"
    if cleaned in ["PB", "LEAD"]:
        return "PB"
    return None

def calculate_pollutant_sub_index(pollutant: str, concentration: Optional[float]) -> Optional[float]:
    """
    Calculate the sub-index for a specific pollutant concentration using official CPCB formula:
        I_p = ((I_Hi - I_Lo) / (B_Hi - B_Lo)) * (C_p - B_Lo) + I_Lo

    Returns:
        float rounded to 1 decimal place, or None if invalid/unsupported/negative.
    """
    if concentration is None:
        return None
    try:
        val = float(concentration)
    except (ValueError, TypeError):
        return None

    if math.isnan(val) or math.isinf(val) or val < 0.0:
        return None

    pollutant_key = normalize_pollutant_name(pollutant)
    if not pollutant_key or pollutant_key not in CPCB_BREAKPOINTS:
        return None

    breakpoints = CPCB_BREAKPOINTS[pollutant_key]

    # Exactly 0 concentration
    if val == 0.0:
        return 0.0

    # Search within standard breakpoint intervals
    for b_lo, b_hi, i_lo, i_hi in breakpoints:
        if b_lo <= val <= b_hi:
            sub_index = ((i_hi - i_lo) / (b_hi - b_lo)) * (val - b_lo) + i_lo
            return round(sub_index, 1)

    # If concentration exceeds highest breakpoint
    last_b_lo, last_b_hi, last_i_lo, last_i_hi = breakpoints[-1]
    if val > last_b_hi:
        sub_index = ((last_i_hi - last_i_lo) / (last_b_hi - last_b_lo)) * (val - last_b_lo) + last_i_lo
        return min(500.0, round(sub_index, 1))

    # Fallback if in a boundary gap due to float precision (e.g. between 30.0 and 30.1)
    for idx in range(len(breakpoints) - 1):
        prev_hi = breakpoints[idx][1]
        next_lo = breakpoints[idx + 1][0]
        if prev_hi < val < next_lo:
            # Map to the next interval's lower bound index
            return round(breakpoints[idx + 1][2], 1)

    return None

def check_averaging_completeness(
    pollutant: str,
    valid_hours: int,
    total_hours: Optional[int] = None
) -> Tuple[bool, float, str]:
    """
    Verify minimum data availability according to CPCB regulations:
    - 24h averaging window (PM2.5, PM10, NO2, SO2, NH3, Pb): minimum 16 hours required (>= 66.7%).
    - 8h averaging window (CO, O3): minimum 6 hours required (>= 75.0%).

    Returns:
        Tuple: (is_eligible, completeness_percentage, averaging_period)
    """
    key = normalize_pollutant_name(pollutant) or pollutant
    period = POLLUTANT_AVERAGING_PERIODS.get(key, "24h")

    if period == "8h":
        expected = total_hours if total_hours else 8
        pct = (valid_hours / expected) * 100.0 if expected > 0 else 0.0
        return (valid_hours >= 6 and pct >= 75.0, round(pct, 1), period)
    else:
        expected = total_hours if total_hours else 24
        pct = (valid_hours / expected) * 100.0 if expected > 0 else 0.0
        return (valid_hours >= 16 and pct >= 66.6, round(pct, 1), period)

def get_aqi_category(aqi_value: Optional[float]) -> Tuple[str, str, str]:
    """
    Get category name, hex color code, and health advisory for a given AQI value.
    Returns: (category_name, hex_color, health_advisory)
    """
    if aqi_value is None or math.isnan(aqi_value) or aqi_value < 0:
        return ("Insufficient Data", "#6B7280", "Data is insufficient to compute an official AQI under CPCB guidelines.")

    for min_val, max_val, category, color, advisory in AQI_CATEGORIES:
        if min_val <= aqi_value <= max_val:
            return (category, color, advisory)

    if aqi_value > 500:
        return ("Severe", "#7F1D1D", "Emergency health warning. Stay indoors.")

    return ("Good", "#10B981", "Minimal impact. Air quality is considered satisfactory.")

def calculate_cpcb_aqi(
    pollutants: Dict[str, Optional[float]],
    strict_eligibility: bool = True
) -> Dict[str, Any]:
    """
    Compute official CPCB AQI from dictionary of pollutant concentrations.

    Strict CPCB Eligibility Gate:
    1. Overall AQI requires monitoring of at least 3 pollutants.
    2. At least one of the pollutants MUST be a particulate matter (PM2.5 or PM10).
    3. Missing pollutants MUST NOT be imputed to 0.

    Args:
        pollutants: Dict of {pollutant_name: concentration}
        strict_eligibility: If True (default), enforces >=3 pollutants with >=1 PM.

    Returns:
        Dict containing aqi, category, color, health_advisory, dominant_pollutant,
        sub_indices, eligible, method_version, and eligibility_reason.
    """
    sub_indices: Dict[str, float] = {}
    valid_pollutants: List[str] = []

    for pol, conc in pollutants.items():
        if conc is not None:
            norm_name = normalize_pollutant_name(pol)
            if norm_name:
                si = calculate_pollutant_sub_index(norm_name, conc)
                if si is not None:
                    sub_indices[norm_name] = si
                    valid_pollutants.append(norm_name)

    has_pm = ("PM2.5" in valid_pollutants) or ("PM10" in valid_pollutants)
    count = len(valid_pollutants)

    if strict_eligibility:
        if count < 3 or not has_pm:
            reason = []
            if count < 3:
                reason.append(f"Insufficient pollutant count ({count}/3 required)")
            if not has_pm:
                reason.append("Missing mandatory particulate matter observation (PM2.5 or PM10)")
            eligibility_msg = "; ".join(reason)

            return {
                "aqi": None,
                "category": "Insufficient Data",
                "color": "#6B7280",
                "health_advisory": f"CPCB AQI cannot be determined: {eligibility_msg}.",
                "dominant_pollutant": None,
                "sub_indices": sub_indices,
                "eligible": False,
                "eligibility_reason": eligibility_msg,
                "method_version": CPCB_METHOD_VERSION,
                "valid_pollutants_count": count
            }

    if not sub_indices:
        return {
            "aqi": None,
            "category": "Insufficient Data",
            "color": "#6B7280",
            "health_advisory": "No valid pollutant measurements provided.",
            "dominant_pollutant": None,
            "sub_indices": {},
            "eligible": False,
            "eligibility_reason": "No valid pollutant data",
            "method_version": CPCB_METHOD_VERSION,
            "valid_pollutants_count": 0
        }

    # Deterministic tie-breaking for dominant pollutant:
    # Find max sub-index, tie-break by POLLUTANT_PRIORITY
    max_si = max(sub_indices.values())
    tied_candidates = [p for p, si in sub_indices.items() if math.isclose(si, max_si, abs_tol=1e-3)]

    dominant_pollutant = tied_candidates[0]
    for p in POLLUTANT_PRIORITY:
        if p in tied_candidates:
            dominant_pollutant = p
            break

    overall_aqi = round(max_si)
    category, color, advisory = get_aqi_category(overall_aqi)

    return {
        "aqi": overall_aqi,
        "category": category,
        "color": color,
        "health_advisory": advisory,
        "dominant_pollutant": dominant_pollutant,
        "sub_indices": sub_indices,
        "eligible": True,
        "eligibility_reason": "Passes official CPCB minimum criteria (>=3 pollutants including PM2.5 or PM10)",
        "method_version": CPCB_METHOD_VERSION,
        "valid_pollutants_count": count
    }
