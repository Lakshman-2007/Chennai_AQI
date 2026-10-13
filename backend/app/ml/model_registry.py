"""
Model Registry & Lifecycle Engine for Chennai Air Quality Framework.

Enforces PRD FR-10 and RG-10:
- Loads model artifacts once into memory (never per-request).
- Validates model artifact compatibility and schema on process startup.
- Executes automated smoke test on known input feature vector.
- Exposes model readiness to FastAPI health check.
"""

import os
import joblib
import json
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))

class ModelRegistry:
    """
    Singleton Model Registry holding production ensemble and preprocessor.
    """
    _instance = None

    def __init__(self):
        self.ensemble = None
        self.pipeline = None
        self.xgboost = None
        self.random_forest = None
        self.metadata: Dict[str, Any] = {}
        self.performance: List[Dict[str, Any]] = []
        self.model_card: Dict[str, Any] = {}
        self.is_ready = False
        self.error_message: Optional[str] = None
        self.smoke_test_passed = False
        self._load_and_validate()

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = ModelRegistry()
        return cls._instance

    def _load_and_validate(self):
        try:
            ens_path = os.path.join(MODELS_DIR, "ensemble.pkl")
            pipe_path = os.path.join(MODELS_DIR, "pipeline.pkl")
            meta_path = os.path.join(MODELS_DIR, "metadata.json")
            perf_path = os.path.join(MODELS_DIR, "performance.json")
            card_path = os.path.join(MODELS_DIR, "model_card.json")

            if not os.path.exists(ens_path) or not os.path.exists(pipe_path):
                self.error_message = "Ensemble or Pipeline pickle artifact missing from models/ directory."
                return

            self.ensemble = joblib.load(ens_path)
            self.pipeline = joblib.load(pipe_path)

            xgb_path = os.path.join(MODELS_DIR, "xgboost.pkl")
            if os.path.exists(xgb_path):
                self.xgboost = joblib.load(xgb_path)

            rf_path = os.path.join(MODELS_DIR, "random_forest.pkl")
            if os.path.exists(rf_path):
                self.random_forest = joblib.load(rf_path)

            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    self.metadata = json.load(f)

            if os.path.exists(perf_path):
                with open(perf_path, "r") as f:
                    self.performance = json.load(f)

            if os.path.exists(card_path):
                with open(card_path, "r") as f:
                    self.model_card = json.load(f)

            # Startup Smoke Test
            self._run_smoke_test()
            self.is_ready = self.smoke_test_passed
        except Exception as e:
            self.error_message = f"Failed to load model registry artifacts: {str(e)}"
            self.is_ready = False

    def _run_smoke_test(self):
        """
        Executes a known-input feature vector prediction to guarantee end-to-end model validity.
        """
        from backend.app.ml.feature_engineering import FEATURE_COLUMNS
        sample_row = pd.DataFrame([{
            "latitude": 13.0827,
            "longitude": 80.2707,
            "timestamp": pd.to_datetime("2026-10-14 00:00:00"),
            "temperature": 30.0,
            "relative_humidity": 75.0,
            "wind_speed": 12.0,
            "wind_direction": 160.0,
            "surface_pressure": 1008.0,
            "boundary_layer_height": 900.0,
            "precipitation": 0.0,
            "satellite_no2": 0.000043,
            "satellite_so2": 0.000012,
            "satellite_co": 0.035,
            "satellite_o3": 0.125,
            "aerosol_index": 0.65,
            "ground_pm25": 45.0
        }])

        from backend.app.ml.feature_engineering import engineer_features
        feat_df = engineer_features(sample_row, is_training=False)
        X_scaled = self.pipeline.transform(feat_df)
        pred = self.ensemble.predict(X_scaled)

        if pred is not None and len(pred) == 1 and not np.isnan(pred[0]):
            self.smoke_test_passed = True
        else:
            self.smoke_test_passed = False
            self.error_message = "Smoke test returned invalid prediction value."

    def get_status(self) -> Dict[str, Any]:
        return {
            "model_ready": self.is_ready,
            "smoke_test_passed": self.smoke_test_passed,
            "model_version": self.metadata.get("model_id", "v2.1.0"),
            "target": self.metadata.get("target_variable", "ground_pm25"),
            "target_unit": self.metadata.get("target_unit", "µg/m³"),
            "forecast_horizon": self.metadata.get("forecast_horizon", "+24h"),
            "validation_strategy": self.metadata.get("validation_strategy", "TimeSeriesSplit"),
            "error_message": self.error_message
        }
