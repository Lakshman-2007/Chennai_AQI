"""
Feature Engineering Engine for Chennai Air Quality Framework.

Computes:
- Temporal features (hour, day, month, day of week, weekend indicator, seasonal harmonics)
- Meteorological interaction terms (wind vectors U/V, temperature-humidity index, ventilation coefficient)
- Satellite column features (raw, normalized, spatial ratios)
- Lagged pollution indicators (lag 1-day, 3-day, 7-day rolling statistics)
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

FEATURE_COLUMNS = [
    # Temporal
    "day_of_year",
    "month",
    "day_of_week",
    "is_weekend",
    "season_sin",
    "season_cos",
    
    # Meteorological
    "temperature",
    "relative_humidity",
    "wind_speed",
    "wind_direction",
    "wind_u",
    "wind_v",
    "surface_pressure",
    "boundary_layer_height",
    "precipitation",
    "temp_humidity_index",
    "ventilation_coefficient",
    
    # Satellite Atmospheric Column Features
    "satellite_no2",
    "satellite_so2",
    "satellite_co",
    "satellite_o3",
    "aerosol_index",
    
    # Geographic & Spatial
    "latitude",
    "longitude",
    
    # History & Rolling (where available)
    "pm25_lag_1d",
    "pm25_rolling_7d_mean"
]

def engineer_features(df: pd.DataFrame, is_training: bool = False) -> pd.DataFrame:
    """
    Transforms raw multi-source dataframe into a clean, model-ready feature dataframe.
    """
    data = df.copy()
    
    # Convert timestamp
    if not pd.api.types.is_datetime64_any_dtype(data["timestamp"]):
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        
    # 1. Temporal Features
    data["day_of_year"] = data["timestamp"].dt.dayofyear
    data["month"] = data["timestamp"].dt.month
    data["day_of_week"] = data["timestamp"].dt.dayofweek
    data["is_weekend"] = (data["day_of_week"] >= 5).astype(int)
    
    # Seasonal sine/cosine cycles
    data["season_sin"] = np.sin(2 * np.pi * data["day_of_year"] / 365.25)
    data["season_cos"] = np.cos(2 * np.pi * data["day_of_year"] / 365.25)
    
    # 2. Meteorological Interaction Features
    rad_dir = np.radians(data["wind_direction"])
    data["wind_u"] = -data["wind_speed"] * np.sin(rad_dir)
    data["wind_v"] = -data["wind_speed"] * np.cos(rad_dir)
    
    data["temp_humidity_index"] = data["temperature"] * (1.0 + data["relative_humidity"] / 100.0)
    data["ventilation_coefficient"] = data["wind_speed"] * (data["boundary_layer_height"] / 1000.0)
    
    # 3. Lagged and Rolling Features (Station-level grouped)
    if "ground_pm25" in data.columns and "station_id" in data.columns:
        data.sort_values(by=["station_id", "timestamp"], inplace=True)
        data["pm25_lag_1d"] = data.groupby("station_id")["ground_pm25"].shift(1)
        data["pm25_rolling_7d_mean"] = data.groupby("station_id")["ground_pm25"].transform(lambda x: x.shift(1).rolling(7, min_periods=1).mean())
    else:
        # For spatial grid prediction where ground history is absent
        data["pm25_lag_1d"] = data.get("ground_pm25", 40.0)
        data["pm25_rolling_7d_mean"] = data.get("ground_pm25", 42.0)
        
    # Fill remaining missing lag values cleanly
    data["pm25_lag_1d"] = data["pm25_lag_1d"].fillna(40.0)
    data["pm25_rolling_7d_mean"] = data["pm25_rolling_7d_mean"].fillna(42.0)
    
    data.sort_values(by="timestamp", inplace=True)
    data.reset_index(drop=True, inplace=True)
    
    return data

class PreprocessingPipeline:
    """
    Encapsulates Imputer and Scaler fitted strictly on training data.
    """
    def __init__(self, feature_cols: List[str] = None):
        self.feature_cols = feature_cols or FEATURE_COLUMNS
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def fit(self, X: pd.DataFrame) -> "PreprocessingPipeline":
        X_sub = X[self.feature_cols]
        X_imp = self.imputer.fit_transform(X_sub)
        self.scaler.fit(X_imp)
        self.is_fitted = True
        return self
        
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before transforming data.")
        X_sub = X[self.feature_cols]
        X_imp = self.imputer.transform(X_sub)
        return self.scaler.transform(X_imp)
        
    def transform_unscaled(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before transforming data.")
        X_sub = X[self.feature_cols]
        return self.imputer.transform(X_sub)
