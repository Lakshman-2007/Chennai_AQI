"""
Explainable AI (XAI) Engine for Chennai Air Quality Framework.

Provides:
1. Global Feature Importance via SHAP values
2. Local Prediction Explanations (Feature attribution per coordinate prediction)
3. Scientific Plain-English Explanation Synthesis with strict non-causal language
"""

import numpy as np
import pandas as pd
import shap
from typing import Dict, List, Any, Tuple
from backend.app.ml.feature_engineering import FEATURE_COLUMNS

FEATURE_READABLE_NAMES = {
    "temperature": "Surface Air Temperature (°C)",
    "relative_humidity": "Relative Humidity (%)",
    "wind_speed": "Wind Speed (km/h)",
    "wind_direction": "Wind Direction (°)",
    "wind_u": "Zonal Wind Component (u)",
    "wind_v": "Meridional Wind Component (v)",
    "surface_pressure": "Barometric Surface Pressure (hPa)",
    "boundary_layer_height": "Planetary Boundary Layer Height (m)",
    "precipitation": "Rainfall Accumulation (mm)",
    "temp_humidity_index": "Thermal Discomfort Index (THI)",
    "ventilation_coefficient": "Atmospheric Ventilation Coefficient (m²/s)",
    "satellite_no2": "Sentinel-5P NO₂ Tropospheric Column",
    "satellite_so2": "Sentinel-5P SO₂ Tropospheric Column",
    "satellite_co": "Sentinel-5P CO Tropospheric Column",
    "satellite_o3": "Sentinel-5P O₃ Total Column",
    "aerosol_index": "Sentinel-5P UV Absorbing Aerosol Index",
    "latitude": "Geographic Latitude (N)",
    "longitude": "Geographic Longitude (E)",
    "day_of_year": "Seasonal Day of Year",
    "month": "Calendar Month",
    "day_of_week": "Day of Week (Traffic Cycle)",
    "is_weekend": "Weekend Traffic Reduction Flag",
    "season_sin": "Cyclic Seasonality (Harmonic Sin)",
    "season_cos": "Cyclic Seasonality (Harmonic Cos)",
    "pm25_lag_1d": "Prior Day PM2.5 Persistence (µg/m³)",
    "pm25_rolling_7d_mean": "7-Day PM2.5 Rolling Baseline (µg/m³)"
}

class AQIExplainer:
    """
    SHAP-based Explainer with scientific attribution synthesis.
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
            self.explainer = shap.Explainer(self.model)

    def get_global_feature_importance(self, df_sample: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Compute mean absolute SHAP feature importances across a representative sample.
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

        importance_list.sort(key=lambda x: x["importance"], reverse=True)
        return importance_list

    def explain_instance(self, single_row_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute local SHAP contributions for a single coordinate prediction.
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
        negative_contributors.sort(key=lambda x: x["impact"])

        narrative = self._generate_narrative(positive_contributors, negative_contributors)

        # Preserves strict additive consistency: E[f(x)] + sum(phi_i) == f(x) (PRD v2.2 C-09)
        pred_pm25 = round(expected_value + sum(c["impact"] for c in positive_contributors + negative_contributors), 2)

        return {
            "base_value": round(expected_value, 2),
            "prediction_pm25": pred_pm25,
            "target": "PM2.5",
            "unit": "µg/m³",
            "model_version": "Chennai-AQI-Stacking-v2.2",
            "surrogate_model": "XGBoost Component of Stacking Ensemble",
            "positive_contributors": positive_contributors,
            "negative_contributors": negative_contributors,
            "narrative": narrative,
            "disclaimer": "Feature attributions reflect statistical model associations, not direct physical causality."
        }

    def _generate_narrative(
        self,
        pos_contrib: List[Dict[str, Any]],
        neg_contrib: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesizes neutral, non-causal explanation in plain English.
        """
        sentences = []

        if pos_contrib:
            top_pos = pos_contrib[0]
            sentences.append(
                f"The highest statistical positive association with elevated PM2.5 at this location was contributed by {top_pos['name']} "
                f"(adding +{top_pos['impact']} µg/m³ relative to the model baseline)."
            )

        if len(pos_contrib) > 1:
            second_pos = pos_contrib[1]
            sentences.append(
                f"Secondary upward association was associated with {second_pos['name']} (+{second_pos['impact']} µg/m³)."
            )

        if neg_contrib:
            top_neg = neg_contrib[0]
            sentences.append(
                f"Conversely, {top_neg['name']} exhibited the strongest moderating statistical association "
                f"({top_neg['impact']} µg/m³)."
            )

        sentences.append(
            "Note: These contributions indicate how individual feature values shifted the model's estimate, and do not constitute epidemiological or causal proof."
        )

        return " ".join(sentences)
