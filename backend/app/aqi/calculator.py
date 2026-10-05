"""
Official CPCB Air Quality Index Calculator Module.

Calculates pollutant sub-indices and overall AQI for ground concentrations.
"""

from typing import Dict, Optional, Tuple, Any
from backend.app.aqi.breakpoints import CPCB_BREAKPOINTS, AQI_CATEGORIES

def calculate_pollutant_sub_index(pollutant: str, concentration: float) -> Optional[float]:
    """
    Calculate the sub-index for a specific pollutant concentration using official CPCB formula.
    """
    if concentration is None or concentration < 0:
        return None
    
    pollutant_key = pollutant.upper().replace(".", "")
    if pollutant_key not in CPCB_BREAKPOINTS:
        # Check alternate key names
        if pollutant_key in ["PM25", "PM2_5"]:
            pollutant_key = "PM2.5"
        else:
            return None
    else:
        pollutant_key = pollutant_key if pollutant_key in CPCB_BREAKPOINTS else "PM2.5"

    breakpoints = CPCB_BREAKPOINTS[pollutant_key]
    
    for b_lo, b_hi, i_lo, i_hi in breakpoints:
        if b_lo <= concentration <= b_hi:
            sub_index = ((i_hi - i_lo) / (b_hi - b_lo)) * (concentration - b_lo) + i_lo
            return round(sub_index, 1)
            
    # Handle concentrations exceeding maximum breakpoint
    last_b_lo, last_b_hi, last_i_lo, last_i_hi = breakpoints[-1]
    if concentration > last_b_hi:
        sub_index = ((last_i_hi - last_i_lo) / (last_b_hi - last_b_lo)) * (concentration - last_b_lo) + last_i_lo
        return min(500.0, round(sub_index, 1))
        
    return None

def get_aqi_category(aqi_value: float) -> Tuple[str, str, str]:
    """
    Get category name, hex color code, and health warning advisory for a given AQI value.
    Returns: (category_name, hex_color, health_advisory)
    """
    if aqi_value is None or aqi_value < 0:
        return ("Unknown", "#6B7280", "No data available")
        
    for min_val, max_val, category, color, advisory in AQI_CATEGORIES:
        if min_val <= aqi_value <= max_val:
            return (category, color, advisory)
            
    if aqi_value > 500:
        return ("Severe", "#7F1D1D", "Emergency health warning. Stay indoors.")
        
    return ("Good", "#10B981", "Air quality is good.")

def calculate_cpcb_aqi(pollutants: Dict[str, float]) -> Dict[str, Any]:
    """
    Compute overall CPCB AQI from a dictionary of pollutant concentrations.
    Must contain at least PM2.5 or PM10 plus at least one other pollutant for official validity.
    """
    sub_indices: Dict[str, float] = {}
    
    for pol, conc in pollutants.items():
        if conc is not None:
            si = calculate_pollutant_sub_index(pol, conc)
            if si is not None:
                sub_indices[pol] = si
                
    if not sub_indices:
        return {
            "aqi": None,
            "category": "Unknown",
            "color": "#6B7280",
            "health_advisory": "Insufficient pollutant data",
            "dominant_pollutant": None,
            "sub_indices": {}
        }
        
    # Find maximum sub-index as overall AQI
    dominant_pollutant = max(sub_indices, key=sub_indices.get) # type: ignore
    overall_aqi = round(sub_indices[dominant_pollutant], 1)
    
    category, color, advisory = get_aqi_category(overall_aqi)
    
    return {
        "aqi": overall_aqi,
        "category": category,
        "color": color,
        "health_advisory": advisory,
        "dominant_pollutant": dominant_pollutant,
        "sub_indices": sub_indices
    }
