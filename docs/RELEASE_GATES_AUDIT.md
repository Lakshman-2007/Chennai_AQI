# Operational Release Gates Audit & Compliance Matrix

**Document Reference:** PRD Version 2.1 — Binding Engineering Amendments & Release Gates  
**Evaluation Date:** October 2026  
**Status:** **ALL GATES PASS (11/11)**  

---

| Gate ID | Release Gate Name | Mandatory Acceptance Requirement | Evidence & Verification Code | Status |
| :---: | :--- | :--- | :--- | :---: |
| **RG-01** | Data Provenance | Canonical schema with SHA-256 digests, units, time range, station coverage, and explicit `observed` vs `synthetic` labels. | `backend/app/schemas/canonical.py`, `backend/app/data_sources/cpcb_adapter.py`. Seeded data strictly labeled `demo`/`synthetic`. | **PASS** |
| **RG-02** | 48-Hour Ingestion Fallback | Activated official manual CSV import path with row-level rejection reporting and SHA-256 manifest. | `backend/app/data_sources/cpcb_adapter.py`, `test_api.py::test_data_sources_endpoints`, UI manual upload modal in `DataSourcesPage.tsx`. | **PASS** |
| **RG-03** | AQI Correctness | Official CPCB NAQI breakpoints, sub-index interpolation, minimum 3 pollutants eligibility with mandatory PM2.5/PM10. | `backend/app/aqi/calculator.py`, `backend/tests/test_aqi_cpcb.py` (10 passing tests verifying boundaries, nulls, and eligibility). | **PASS** |
| **RG-04** | Point-in-Time Features | Target future $\text{valid\_at} > \text{issued\_at}$; no lookahead leakage in features or lags. | `backend/app/ml/spatial.py`, `test_api.py::test_prediction_map_endpoint`, `test_api.py::test_prediction_point_endpoint`. | **PASS** |
| **RG-05** | Stacking Validation | Chronological holdout + 5-fold walk-forward `TimeSeriesSplit` meta-learner training. Zero random K-fold or shuffling in pipeline. | `backend/app/ml/trainer.py` (`WalkForwardStackingEnsemble`), `models/metadata.json`. | **PASS** |
| **RG-06** | Model Utility Benchmark | Model demonstrates meaningful improvement over Persistence (Lag-1D) and Seasonal-Naive baselines on holdout set. | `models/performance.json`: Stacking RMSE $6.45$ vs Persistence RMSE $19.12$ ($66.26\%$ improvement). | **PASS** |
| **RG-07** | Freshness UX/API | Freshness TTL state machine ($\le 2\text{h}$ fresh, $\le 24\text{h}$ stale, $> 24\text{h}$ expired). Badges and API metadata rendered consistently. | `backend/app/data_processing/store.py`, `ScientificAlert.tsx`, `DataSourcesPage.tsx`, `backend/tests/test_api.py`. | **PASS** |
| **RG-08** | Spatial Integrity | Explicit `EPSG:4326` CRS on all geometries; GCC 15 zones administrative boundary GeoJSON; gazetteer with 30+ localities. | `backend/app/data_sources/chennai_gis_adapter.py`, `backend/app/api/gis.py`, `test_api.py::test_gis_endpoints`. | **PASS** |
| **RG-09** | Satellite Decoupling | Disabling satellite credentials/feed does not break core AQI, ground station ingestion, or ML inference. | `backend/app/data_sources/sentinel5p_adapter.py` decoupled; offline contextual role only (PRD 21.6). | **PASS** |
| **RG-10** | Artifact Compatibility | Process startup smoke test verifying loaded pipeline and weights; health check reports model readiness. | `backend/app/ml/model_registry.py` (`_run_smoke_test`), `test_api.py::test_health_endpoint`. | **PASS** |
| **RG-11** | Reproducibility | Clean environment builds with 100% passing backend pytest tests (26/26) and 100% passing frontend build. | `pytest backend/tests` (26 passed), `npm run build` (tsc -b && vite build passed). | **PASS** |
