# Hybrid Explainable Multi-Source Air Quality Prediction Framework for Chennai

**Project Title:** Hybrid Explainable Multi-Source Air Quality Prediction Framework for Chennai using Sentinel-5P Satellite Data, Ground Monitoring Stations, Meteorological Data, and Ensemble Machine Learning

---

## 🌟 Overview & Key Highlights

This application provides a technically defensible, end-to-end environmental intelligence framework specifically tailored for **Chennai, Tamil Nadu, India** ($12.75^\circ\text{N} - 13.25^\circ\text{N}, 80.05^\circ\text{E} - 80.35^\circ\text{E}$).

### 🔬 Strict Scientific Principles
- **Atmospheric Column Density vs. Ground Concentration**: Sentinel-5P satellite observations ($\text{NO}_2$, $\text{SO}_2$, $\text{CO}$, $\text{O}_3$, Aerosol Index column number densities in $\text{mol/m}^2$) are treated strictly as **predictive input features** to ML models, NOT ground-level concentrations.
- **Official CPCB Sub-Index Methodology**: Ground pollutant predictions ($\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, $\text{SO}_2$, $\text{CO}$, $\text{O}_3$) are converted into **Predicted AQI** using official Central Pollution Control Board (CPCB, India) sub-index equations and breakpoints.
- **Explainable AI (XAI)**: SHAP-based global feature importances and point-wise local attribution with automated plain-English narrative synthesis.
- **Uncertainty Quantification**: 95% confidence prediction intervals $[ \text{Lower}, \text{Upper} ]$ derived from ensemble prediction variance.

---

## 🏗️ Architecture

```text
               MULTI-SOURCE ENVIRONMENTAL DATA
┌───────────────────────┬─────────────────────────┬──────────────────────────┐
│  Sentinel-5P Satellite│ Ground Monitoring (CPCB)│ Surface Weather Physics  │
│  Atmospheric Columns  │ 7 Chennai Stations      │ (Open-Meteo Reanalysis)  │
└───────────┬───────────┴────────────┬────────────┴────────────┬─────────────┘
            │                        │                         │
            └────────────────────────┼─────────────────────────┘
                                     ▼
                          DATA ALIGNMENT PIPELINE
                    (Spatial Grid & Hourly Windows)
                                     │
                                     ▼
                         FEATURE ENGINEERING ENGINE
            (Lags, Rolling Stats, Wind U/V, Ventilation Coeff)
                                     │
                                     ▼
                      MULTI-MODEL STACKING ENSEMBLE
   [Linear, Tree, Random Forest, ExtraTrees, GradientBoosting, XGBoost, LightGBM, CatBoost]
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
      EXPLAINABLE AI ENGINE                   SPATIAL INFERENCE GRID
     (SHAP & Local Attribution)               (Chennai Grid & Hotspots)
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
                              FASTAPI BACKEND
                           (REST APIs / Uvicorn)
                                     │
                                     ▼
                         REACT + TYPESCRIPT DASHBOARD
                  (Tailwind CSS + Leaflet + Recharts)
```

---

## 📊 ML Benchmark Results (Chennai Evaluation Set)

| Model Architecture | R² Score | RMSE (µg/m³) | MAE (µg/m³) | MAPE (%) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Stacking Meta-Ensemble** | **0.8789** | **6.54** | **5.25** | **15.08%** | **Champion** |
| CatBoost Regressor | 0.8786 | 6.54 | 5.38 | 14.64% | Candidate |
| XGBoost Regressor | 0.8759 | 6.62 | 5.37 | 14.83% | Candidate |
| Gradient Boosting | 0.8754 | 6.63 | 5.41 | 14.82% | Candidate |
| LightGBM Regressor | 0.8752 | 6.63 | 5.40 | 14.80% | Candidate |
| Extra Trees Regressor | 0.8675 | 6.84 | 5.52 | 15.35% | Candidate |
| Linear Regression | 0.8586 | 7.06 | 5.36 | 16.44% | Candidate |
| Random Forest Regressor | 0.8543 | 7.17 | 5.76 | 16.51% | Candidate |
| Decision Tree Regressor | 0.6699 | 10.79 | 8.34 | 23.21% | Candidate |

---

## 🚀 Quick Start & Installation Guide

### Prerequisites
- Python 3.10+
- Node.js v18+ & npm v9+

### 1. Setup & Run Backend API
```bash
# From project root
python scripts/train_model.py     # Generates dataset & trains ensemble artifacts into models/
python -m pytest backend/tests/   # Runs backend automated unit test suite

# Start FastAPI Uvicorn Server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Backend API interactive Swagger docs available at: `http://localhost:8000/docs`

### 2. Setup & Run Frontend Application
```bash
# Navigate to frontend directory
cd frontend
npm install
npm run dev
```
Frontend dashboard accessible at: `http://localhost:3000`

---

## 🧪 Automated Tests
Run full backend test suite:
```bash
python -m pytest backend/tests/
```
Verify frontend build compilation:
```bash
cd frontend && npm run build
```

---

## 📄 License & Attribution
- Data Sources: ESA Copernicus Sentinel-5P, CPCB India CAAQMS, Open-Meteo Weather API.
- Developed for scientific research & academic project demonstration.
