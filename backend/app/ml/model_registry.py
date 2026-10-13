"""
Model Registry & Lifecycle Engine for Chennai Air Quality Framework.

Conforms to PRD v2.3 REQ-MODEL-02:
- Explicit lifecycle states: 'not_loaded', 'loading', 'ready', 'failed'.
- Decouples core prediction model readiness from optional explainer readiness.
- Validates model artifact compatibility and feature schema.
- Executes automated deterministic smoke test with known-good feature fixture.
- Logs internal diagnostic details securely without leaking filesystem paths to public API responses.
"""

import os
import joblib
import json
import logging
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd

logger = logging.getLogger("chennai_aqi.registry")
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))

class ModelRegistry:
    """
    Singleton Model Registry holding production ensemble, preprocessor, and explainer.
    Enforces explicit lifecycle states and decoupled capabilities.
    """
    _instance = None

    def __init__(self):
        self.state: str = "not_loaded"  # not_loaded | loading | ready | failed
        self.ensemble = None
        self.pipeline = None
        self.xgboost = None
        self.random_forest = None
        self.metadata: Dict[str, Any] = {}
        self.performance: List[Dict[str, Any]] = []
        self.model_card: Dict[str, Any] = {}

        self.core_model_ready: bool = False
        self.explainer_ready: bool = False
        self.smoke_test_passed: bool = False

        self.safe_error_code: str = "NONE"
        self.safe_error_message: Optional[str] = None
        self.internal_error_log: Optional[str] = None

        self._load_and_validate()

    @property
    def is_ready(self) -> bool:
        """Backward-compatible alias pointing to core model readiness."""
        return self.core_model_ready

    @property
    def error_message(self) -> Optional[str]:
        """Backward-compatible alias returning safe public error message."""
        return self.safe_error_message

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = ModelRegistry()
        return cls._instance

    def _load_and_validate(self):
        self.state = "loading"
        ens_path = os.path.join(MODELS_DIR, "ensemble.pkl")
        pipe_path = os.path.join(MODELS_DIR, "pipeline.pkl")
        meta_path = os.path.join(MODELS_DIR, "metadata.json")
        perf_path = os.path.join(MODELS_DIR, "performance.json")
        card_path = os.path.join(MODELS_DIR, "model_card.json")
        xgb_path = os.path.join(MODELS_DIR, "xgboost.pkl")
        rf_path = os.path.join(MODELS_DIR, "random_forest.pkl")

        # 1. Validate and Load Core Prediction Artifacts
        try:
            if not os.path.exists(ens_path) or not os.path.exists(pipe_path):
                missing = [p for p in [ens_path, pipe_path] if not os.path.exists(p)]
                self.internal_error_log = f"Missing core artifact files: {missing}"
                logger.error(self.internal_error_log)
                self.safe_error_code = "MODEL_NOT_READY"
                self.safe_error_message = "Core prediction artifacts are missing or uninitialized."
                self.state = "failed"
                self.core_model_ready = False
                return

            self.ensemble = joblib.load(ens_path)
            self.pipeline = joblib.load(pipe_path)

            if not hasattr(self.ensemble, "predict") or not hasattr(self.pipeline, "transform"):
                self.internal_error_log = "Loaded core artifacts do not expose required predict/transform interfaces."
                logger.error(self.internal_error_log)
                self.safe_error_code = "MODEL_NOT_READY"
                self.safe_error_message = "Loaded model artifacts failed interface validation."
                self.state = "failed"
                self.core_model_ready = False
                return

            # Metadata and Model Cards
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)

            if os.path.exists(perf_path):
                with open(perf_path, "r", encoding="utf-8") as f:
                    self.performance = json.load(f)

            if os.path.exists(card_path):
                with open(card_path, "r", encoding="utf-8") as f:
                    self.model_card = json.load(f)

            # Startup Smoke Test for Core Model
            self._run_smoke_test()
            if self.smoke_test_passed:
                self.core_model_ready = True
                self.state = "ready"
                self.safe_error_code = "NONE"
                self.safe_error_message = None
            else:
                self.core_model_ready = False
                self.state = "failed"

        except Exception as e:
            self.internal_error_log = f"Exception loading core model registry artifacts: {str(e)}"
            logger.error(self.internal_error_log, exc_info=True)
            self.safe_error_code = "MODEL_NOT_READY"
            self.safe_error_message = "Failed to deserialize or initialize prediction models."
            self.state = "failed"
            self.core_model_ready = False

        # 2. Independently Validate Optional Explainer Artifact (REQ-MODEL-02 decoupling)
        try:
            if os.path.exists(xgb_path):
                self.xgboost = joblib.load(xgb_path)
                if hasattr(self.xgboost, "predict"):
                    self.explainer_ready = True
                else:
                    self.explainer_ready = False
            else:
                self.explainer_ready = False
                logger.warning("Optional XGBoost explainer artifact not found; XAI routes will report explainer unready.")

            if os.path.exists(rf_path):
                self.random_forest = joblib.load(rf_path)

        except Exception as e:
            logger.warning(f"Optional explainer artifact load failed: {str(e)}")
            self.explainer_ready = False

    def _run_smoke_test(self):
        """
        Executes a known-input feature vector prediction to guarantee end-to-end model validity.
        Verifies output shape and mathematical finiteness.
        """
        try:
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

            if pred is not None and len(pred) == 1 and np.isfinite(pred[0]):
                self.smoke_test_passed = True
            else:
                self.smoke_test_passed = False
                self.safe_error_code = "SMOKE_TEST_FAILED"
                self.safe_error_message = "Model smoke prediction returned non-finite value."
                logger.error("Smoke test produced non-finite or empty prediction.")
        except Exception as e:
            self.smoke_test_passed = False
            self.safe_error_code = "SMOKE_TEST_EXCEPTION"
            self.safe_error_message = "Exception occurred during model smoke test."
            logger.error(f"Smoke test execution exception: {str(e)}", exc_info=True)

    def set_unready_for_test(self, core: bool = False, explainer: bool = False):
        """Test fixture helper to simulate unready states safely."""
        self.core_model_ready = not core
        self.explainer_ready = not explainer
        if not self.core_model_ready:
            self.state = "failed"
            self.safe_error_code = "MODEL_NOT_READY"
            self.safe_error_message = "Test simulation: model unready."

    def reset_for_test(self):
        """Restores genuine loaded state after testing."""
        self._load_and_validate()

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "model_ready": self.core_model_ready,
            "core_model_ready": self.core_model_ready,
            "explainer_ready": self.explainer_ready,
            "smoke_test_passed": self.smoke_test_passed,
            "model_version": self.metadata.get("model_id", "v2.3.0"),
            "target": self.metadata.get("target_variable", "ground_pm25"),
            "target_unit": self.metadata.get("target_unit", "µg/m³"),
            "forecast_horizon": self.metadata.get("forecast_horizon", "+24h"),
            "validation_strategy": self.metadata.get("validation_strategy", "Timestamp-Grouped Walk-Forward TimeSeriesSplit"),
            "safe_error_code": self.safe_error_code,
            "error_message": self.safe_error_message
        }
