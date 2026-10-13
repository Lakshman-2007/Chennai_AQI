# Release Evidence & Six Failing Tests Resolution Report (v2.3)

**Document Reference:** CHENNAI_AQI PRD v2.3 Six Failing Tests — Fix Specification  
**Evaluation Date:** 13 October 2026  
**Status:** **ALL SIX TARGETED TESTS PASSING (100% GREEN)**  

---

## E-01: Root Cause Analysis & Resolution Log

| Test Name | Root Cause Discovered | Code Location | Resolution Applied |
| :--- | :--- | :--- | :--- |
| `test_health_endpoint` | Process liveness was entangled with model readiness. Health endpoint returned single degraded state without reporting explicit `liveness: "alive"` or safe readiness code when models were unready. | `backend/app/main.py:health_check`, `backend/app/ml/model_registry.py` | Refactored `ModelRegistry` with explicit states (`not_loaded`, `loading`, `ready`, `failed`). Added decoupled health checks (`liveness: "alive"`, `readiness: "ready" \| "model_not_ready"`, `readiness_code: "READY" \| "MODEL_NOT_READY"`), plus dedicated `/api/health/live` and `/api/health/ready` probe endpoints. |
| `test_prediction_point_endpoint` | Model unready condition previously returned unhandled 503 without structured machine-readable error payload. | `backend/app/api/predictions.py:predict_location_point` | Added `ModelNotReadyException` with unified structured error contract: `{"detail": "...", "code": "MODEL_NOT_READY", "error": {"code": "MODEL_NOT_READY", "message": "...", "retryable": false}}`. |
| `test_prediction_map_endpoint` | Query parameter URL encoding for `horizon=+24h` was decoded by starlette as `" 24h"`, failing strict string match. Model readiness checks were coupled to explainer availability. | `backend/app/schemas/schemas.py`, `backend/app/api/predictions.py:get_spatial_prediction_map` | Implemented `normalize_horizon` handling URL space-encoding, returning clean 422 on invalid horizons and 503 `MODEL_NOT_READY` when core models are unready. |
| `test_hotspots_endpoint` | Hotspot endpoint incorrectly depended unconditionally on the ML model registry even when calculating from ground station observations. | `backend/app/api/hotspots.py`, `backend/app/ml/spatial.py:detect_chennai_hotspots` | Decoupled observed data-derived hotspots from ML registry (`source="observed"` uses `DataStore`). Forecast hotspots require `core_model_ready` and return 503 `MODEL_NOT_READY` when unready. Added `layer_type`, `spatial_reference`, and explicit empty array for insufficient data. |
| `test_global_explain_endpoint` | Explainer failure previously collapsed core prediction readiness; responses did not disclose component surrogate identity. | `backend/app/api/explain.py:get_global_explanations`, `backend/app/ml/model_registry.py` | Decoupled `explainer_ready` from `core_model_ready`. If explainer is unready, returns structured 503 `EXPLAINER_NOT_READY` while core predictions remain 100% operational. Response explicitly labels `surrogate_model: "XGBoost Component of Stacking Ensemble"`. |
| `test_point_explain_endpoint` | Slicing contributors to top-6 in backend broke SHAP additive efficiency test ($E[f(x)] + \sum \phi_i = f(x)$). | `backend/app/ml/explainer.py:explain_instance` | Returns full sorted contributor list enabling mathematical additive validation within $0.1\,\mu\text{g/m}^3$ tolerance. Explainer unavailability returns isolated 503 `EXPLAINER_NOT_READY`. |

---

## E-02: Pinned Dependency Environment (Python 3.13.7)

Environment lock generated in [`requirements.lock`](file:///c:/Users/Lakshmana%20Dhityan/Desktop/Full%20chennai%20aqi/requirements.lock):
- Python Version: `3.13.7`
- `scikit-learn`: `1.7.2`
- `joblib`: `1.5.2`
- `xgboost`: `3.4.1`
- `lightgbm`: `4.7.0`
- `catboost`: `1.2.10`
- `shap`: `0.52.0`
- `numpy`: `2.2.6`
- `scipy`: `1.16.2`
- `pandas`: `2.3.2`
- `fastapi`: `0.141.1`
- `pydantic`: `2.9.2`
- `uvicorn`: `0.30.6`

---

## E-03: Real Artifact Load & Deterministic Smoke Test Verification

```
Registry Startup:
- Core Model State: ready
- Preprocessing Pipeline: loaded (26 features)
- Walk-Forward Stacking Ensemble: loaded (8 base regressors + Ridge meta-learner)
- XGBoost Explainer Surrogate: loaded
- Deterministic Smoke Test: PASSED (predict=58.4 µg/m³, finite=True, NaN=False)
- Safe Error Code: NONE
```

---

## E-04: Focused Six Tests Execution Output

```powershell
python -m pytest -q tests/test_health_endpoint.py
# 1 passed in 2.65s

python -m pytest -q tests/test_prediction_map_endpoint.py
# 1 passed in 2.76s

python -m pytest -q tests/test_prediction_point_endpoint.py
# 1 passed in 2.77s

python -m pytest -q tests/test_hotspots_endpoint.py
# 1 passed in 4.34s

python -m pytest -q tests/test_global_explain_endpoint.py
# 1 passed in 2.79s

python -m pytest -q tests/test_point_explain_endpoint.py
# 1 passed in 2.62s
```

All 6 focused test files execute and pass 100%.

---

## E-05: Full Backend Suite Execution Result

```powershell
python -m pytest backend/tests -v
# 26 passed, 1 warning in 9.89s (100% passing)
```

---

## E-06: API Response Contracts & Error Codes

1. **Model Unready Error (503):**
   ```json
   {
     "detail": "Prediction service unavailable: core model artifacts not ready.",
     "code": "MODEL_NOT_READY",
     "error": {
       "code": "MODEL_NOT_READY",
       "message": "Prediction service unavailable: core model artifacts not ready.",
       "retryable": false
     }
   }
   ```

2. **Explainer Unready Error (503):**
   ```json
   {
     "detail": "XAI explainer service unavailable: explainer artifact not ready.",
     "code": "EXPLAINER_NOT_READY",
     "error": {
       "code": "EXPLAINER_NOT_READY",
       "message": "XAI explainer service unavailable: explainer artifact not ready.",
       "retryable": false
     }
   }
   ```

3. **Validation Error (422):**
   - Out-of-bounds coordinates or disallowed horizon (`+3h`) returns HTTP 422 with field validation error details.

---

## E-07: Updated Release Gate Status (Audit Matrix)

- **Total Gates:** 11
- **Operational Pass:** 9 Gates (`RG-02` through `RG-05`, `RG-07` through `RG-11`)
- **Demo / Controlled Pass:** 2 Gates (`RG-01`, `RG-06`)
- **Failing Gates:** 0
