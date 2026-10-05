"""
Explainable AI (XAI) Engine for Chennai Air Quality Framework.

Provides:
1. Global Feature Importance (SHAP summary & mean absolute SHAP values)
2. Local Prediction Explanations (Feature attribution per coordinate prediction)
3. Natural Language Explanation Synthesis
"""

import numpy as np
import pandas as pd
import shap
from typing import Dict, List, Any, Tuple
from backend.app.ml.feature_engineering import FEATURE_COLUMNS

class AQIExplainer:
    """
    SHAP-based Explainer for Tree-based models (XGBoost / Random Forest).
    """
    def __init__(self, model: Any, pipeline: Any):
        self.model = model
        self.pipeline = pipeline
        self.explainer = None
        self._init_explainer()
        
    def _init_explainer(self):
        try:
            self.explainer = shap.TreeExplainer(self.model)
        except Exception:
            # Fallback KernelExplainer / ExactExplainer
            self.explainer = shap.Explainer(self.model)
            
    def get_global_feature_importance(self, df_sample: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Compute mean absolute SHAP feature importances across a sample dataset.
        """
        X_scaled = self.pipeline.transform(df_sample)
        shap_values = self.explainer.shap_values(X_scaled)
        
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
            
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        
        importance_list = []
        for feat_name, imp in zip(FEATURE_COLUMNS, mean_abs_shap):
            readable_name = FEATURE_READABLE_NAMES.get(feat_name, feat_name)
            importance_list.append({
                "feature": feat_name,
                "name": readable_name,
                "importance": round(float(imp), 4)
            })
            
        # Sort descending by importance
        importance_list.sort(key=lambda x: x["importance"], reverse=True)
        return importance_list

    def explain_instance(self, single_row_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute local SHAP contribution for a single location / row prediction.
        """
        X_scaled = self.pipeline.transform(single_row_df)
        shap_vals = self.explainer.shap_values(X_scaled)
        
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[0]
            
        if shap_vals.ndim == 2:
            shap_vals = shap_vals[0]
            
        expected_value = float(self.explainer.expected_value) if hasattr(self.explainer, "expected_value") and not isinstance(self.explainer.expected_value, np.ndarray) else 45.0
        
        positive_contributors = []
        negative_contributors = []
        
        for feat, val in zip(FEATURE_COLUMNS, shap_vals):
            readable = FEATURE_READABLE_NAMES.get(feat, feat)
            impact = round(float(val), 2)
            raw_val = float(single_row_df[feat].iloc[0]) if feat in single_row_df.columns else 0.0
            
            item = {
                "feature": feat,
                "name": readable,
                "impact": impact,
                "raw_value": round(raw_val, 4)
            }
            
            if impact > 0:
                positive_contributors.append(item)
            else:
                negative_contributors.append(item)
                
        positive_contributors.sort(key=lambda x: x["impact"], reverse=True)
        negative_contributors.sort(key=lambda x: x["impact"]) # Most negative first
        
        # Synthesize plain-English narrative explanation
        narrative = self._generate_narrative(positive_contributors, negative_contributors)
        
        return {
            "base_value": round(expected_value, 2),
            "positive_contributors": positive_contributors[:4],
            "negative_contributors": negative_contributors[:4],
            "narrative": narrative
        }

    def _generate_narrative(self, positive: List[Dict], negative: List[Dict]) -> str:
        pos_str = []
        for p in positive[:2]:
            pos_str.append(f"{p['name']} (+{p['impact']} µg/m³)")
            
        neg_str = []
        for n in negative[:2]:
            neg_str.append(f"{n['name']} ({n['impact']} µg/m³)")
            
        pos_part = ", ".join(pos_str) if pos_str else "seasonal factors"
        neg_part = ", ".join(neg_str) if neg_str else "atmospheric dispersion"
        
        return (
            f"The model's prediction for this location is primarily elevated by {pos_part}. "
            f"Conversely, {neg_part} helped mitigate pollutant accumulation."
        )

FEATURE_READABLE_NAMES = {
    "satellite_no2": "Sentinel-5P NO₂ Column Density",
    "satellite_so2": "Sentinel-5P SO₂ Column Density",
    "satellite_co": "Sentinel-5P CO Column Density",
    "satellite_o3": "Sentinel-5P O₃ Column Density",
    "aerosol_index": "Sentinel-5P Aerosol Index",
    "temperature": "Surface Temperature",
    "relative_humidity": "Relative Humidity",
    "wind_speed": "Wind Speed",
    "wind_direction": "Wind Direction",
    "wind_u": "Eastward Wind Vector (U)",
    "wind_v": "Northward Wind Vector (V)",
    "surface_pressure": "Surface Pressure",
    "boundary_layer_height": "Planetary Boundary Layer Height",
    "precipitation": "Precipitation",
    "temp_humidity_index": "Thermal-Humidity Interaction",
    "ventilation_coefficient": "Ventilation Coefficient",
    "pm25_lag_1d": "Previous Day PM2.5 Level",
    "pm25_rolling_7d_mean": "7-Day PM2.5 Moving Average",
    "day_of_year": "Day of Year",
    "month": "Month",
    "day_of_week": "Day of Week",
    "is_weekend": "Weekend Indicator",
    "season_sin": "Seasonal Sine Harmonic",
    "season_cos": "Seasonal Cosine Harmonic",
    "latitude": "Latitude Coordinate",
    "longitude": "Longitude Coordinate"
}
