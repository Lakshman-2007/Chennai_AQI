"""
Script to construct multi-source dataset for Chennai, train base ML models & stacking ensemble, evaluate metrics, and export trained artifacts to models/ directory.
"""

import sys
import os

# Ensure backend path is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.ml.data_loader import generate_chennai_multisource_dataset
from backend.app.ml.trainer import train_aqi_models

def main():
    print("=" * 70)
    print("CHENNAI AQI FRAMEWORK: MULTI-SOURCE DATASET GENERATION & MODEL TRAINING")
    print("=" * 70)
    
    print("\n1. Generating aligned multi-source Chennai dataset (Ground + Sentinel-5P + Weather)...")
    df = generate_chennai_multisource_dataset(start_date="2025-01-01", end_date="2026-03-31", freq="1D", random_seed=42)
    print(f"   - Total aligned records generated: {len(df)}")
    print(f"   - Columns: {list(df.columns)}")
    
    # Save raw/processed dataset
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed"))
    os.makedirs(data_dir, exist_ok=True)
    df.to_csv(os.path.join(data_dir, "chennai_multisource_aligned.csv"), index=False)
    print(f"   - Saved processed dataset to: {os.path.join(data_dir, 'chennai_multisource_aligned.csv')}")
    
    print("\n2. Training candidate models (Linear, DecisionTree, RandomForest, ExtraTrees, GradientBoosting, XGBoost, LightGBM, CatBoost) & Stacking Ensemble...")
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
    results = train_aqi_models(df=df, target_col="ground_pm25", output_dir=output_dir)
    
    print("\n3. Training Summary:")
    print("-" * 50)
    for res in results["comparison"]:
        print(f"   {res['model']:24s} -> R²: {res['r2']:6.4f} | RMSE: {res['rmse']:5.2f} | MAE: {res['mae']:5.2f} | MAPE: {res['mape']:5.2f}%")
        
    print("\n4. Ensemble Meta-Weights:")
    for name, w in results["ensemble_weights"].items():
        print(f"   - {name:20s}: {w*100:5.1f}%")
        
    print("\n" + "=" * 70)
    print("SUCCESS: Trained artifacts successfully exported to models/ directory.")
    print("=" * 70)

if __name__ == "__main__":
    main()
