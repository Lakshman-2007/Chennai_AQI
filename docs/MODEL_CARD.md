# Model Card: Chennai Air Quality PM2.5 Walk-Forward Stacking Ensemble

**Model Name:** Chennai-AQI-Stacking-v2.1  
**Architecture:** 8 Base Candidate Regressors + Ridge Stacking Meta-Learner  
**Target Variable:** Surface $\text{PM}_{2.5}$ Concentration ($\mu\text{g/m}^3$)  
**Forecast Horizon:** $+24\text{h}$ valid interval ahead  
**Release Date:** October 2026  
**License:** MIT  

---

## 1. Intended Use & Target Geography

- **Primary Intended Use:** Prospective forecasting of surface $\text{PM}_{2.5}$ concentration across continuous ambient air quality monitoring stations (CAAQMS) and high-resolution spatial grid cells across Chennai, Tamil Nadu, India.
- **Geographic Bounding Box:**
  - Latitude: $12.75^\circ\text{N} - 13.25^\circ\text{N}$
  - Longitude: $80.05^\circ\text{E} - 80.35^\circ\text{E}$
- **Non-Goals & Scientific Caveats:**
  - Forecast concentrations represent discrete spatial point estimates and must not be confused with regulatory 24-hour composite measurements without sampling completeness.
  - Sentinel-5P satellite tropospheric vertical columns are auxiliary predictor features and must never be treated as direct ground surface observations.

---

## 2. Leakage-Free Validation Methodology (PRD 21.4)

The release model adheres strictly to the normative engineering amendments of Section 21.4:
1. **No Shuffling / No Random K-Fold:** All random data shuffling is strictly prohibited.
2. **Untouched Chronological Holdout:** The latest $20\%$ of chronological data (contiguous temporal split) was strictly reserved and kept untouched prior to model selection and meta-learner fitting.
3. **Walk-Forward TimeSeriesSplit:** Out-Of-Fold (OOF) predictions for the Ridge meta-learner were generated strictly using expanding chronological windows (`TimeSeriesSplit(n_splits=5)`), guaranteeing that no future information ever leaks into historical folds.
4. **Preprocessing Pipelines:** All scalers, imputers, and feature engineering transformations are fitted strictly on the permitted training splits.

---

## 3. Evaluation Metrics vs. Mandatory Baselines

Evaluated on the independent, untouched chronological holdout set ($N = 637$ test samples):

| Model Architecture | R² Score | RMSE ($\mu\text{g/m}^3$) | MAE ($\mu\text{g/m}^3$) | MAPE (%) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline: Persistence (Lag-1D)** | -0.0369 | 19.12 | 14.89 | 42.59% | Regulatory Benchmark |
| **Baseline: Seasonal-Naive** | -0.0005 | 18.79 | 15.16 | 49.42% | Cyclic Benchmark |
| Linear Regression | 0.8586 | 7.06 | 5.36 | 16.44% | Candidate |
| Decision Tree Regressor | 0.6699 | 10.79 | 8.34 | 23.21% | Candidate |
| Random Forest Regressor | 0.8543 | 7.17 | 5.76 | 16.51% | Candidate |
| Extra Trees Regressor | 0.8675 | 6.84 | 5.52 | 15.35% | Candidate |
| Gradient Boosting Regressor | 0.8754 | 6.63 | 5.41 | 14.82% | Candidate |
| XGBoost Regressor | 0.8759 | 6.62 | 5.37 | 14.83% | Candidate |
| LightGBM Regressor | 0.8752 | 6.63 | 5.40 | 14.80% | Candidate |
| CatBoost Regressor | 0.8786 | 6.54 | 5.38 | 14.64% | Candidate |
| **Ensemble (Walk-Forward Stacking)** | **0.8820** | **6.45** | **5.29** | **14.52%** | **Production Champion** |

### Benchmark Improvement
- **RMSE Reduction vs Persistence Baseline:** **$66.26\%$**
- **MAE Reduction vs Persistence Baseline:** **$64.47\%$**

---

## 4. Stacking Meta-Learner Weights

- CatBoost: **$38.4\%$**
- LightGBM: **$29.8\%$**
- Extra Trees: **$20.5\%$**
- Linear Regression: **$8.3\%$**
- Gradient Boosting: **$2.9\%$**

---

## 5. Explainability & Uncertainty Quantification

- **SHAP Feature Attributions:** Calculated using TreeExplainer on tree ensembles.
- **Calibrated Prediction Intervals:** 95% Confidence Intervals computed from base learner prediction variance:
  $$\hat{y} \pm 1.96 \cdot \sigma_{\text{ensemble}}$$
