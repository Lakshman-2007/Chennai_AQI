"""
Data Store & Freshness Management Engine.
Maintains canonical observations, mode management (demo / manual_import / live),
data freshness tracking (fresh <=2h, stale <=24h, expired >24h), and query accessors.
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import pandas as pd

from backend.app.schemas.canonical import (
    DataSourceMode,
    DataStatusEnum,
    FreshnessStatus
)
from backend.app.aqi.calculator import calculate_cpcb_aqi

class DataStore:
    """
    Central Data Repository for Chennai Air Quality Framework.
    Manages in-memory caching and persistent reads of aligned observations.
    """
    _instance = None

    def __init__(self):
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        self.processed_csv_path = os.path.join(
            self.base_dir, "data", "processed", "chennai_multisource_aligned.csv"
        )
        self.manifest_path = os.path.join(
            self.base_dir, "data", "import_manifests.json"
        )
        self._df: Optional[pd.DataFrame] = None
        self._load_data()

    @classmethod
    def get_instance(cls) -> "DataStore":
        if cls._instance is None:
            cls._instance = DataStore()
        return cls._instance

    def _load_data(self):
        if os.path.exists(self.processed_csv_path):
            self._df = pd.read_csv(self.processed_csv_path)
            self._df["timestamp"] = pd.to_datetime(self._df["timestamp"])
            self._df.sort_values(by=["timestamp", "station_id"], inplace=True)

    def reload(self):
        self._load_data()

    def get_mode(self) -> DataSourceMode:
        """Determines active operational mode."""
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r") as f:
                    manifests = json.load(f)
                    if manifests and len(manifests) > 0:
                        return DataSourceMode.MANUAL_IMPORT
            except Exception:
                pass
        return DataSourceMode.DEMO

    def get_data_status(self) -> DataStatusEnum:
        mode = self.get_mode()
        if mode == DataSourceMode.MANUAL_IMPORT:
            return DataStatusEnum.MANUAL_IMPORT
        elif mode == DataSourceMode.LIVE:
            return DataStatusEnum.OBSERVED
        return DataStatusEnum.SYNTHETIC

    def calculate_freshness(self, observed_at: datetime) -> Tuple[FreshnessStatus, float]:
        now = datetime.now(timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        age_seconds = (now - observed_at).total_seconds()

        # Ensure age is positive
        age_seconds = max(0.0, age_seconds)

        if age_seconds <= 2 * 3600:
            return FreshnessStatus.FRESH, age_seconds
        elif age_seconds <= 24 * 3600:
            return FreshnessStatus.STALE, age_seconds
        else:
            return FreshnessStatus.EXPIRED, age_seconds

    def get_overview(self) -> Dict[str, Any]:
        """
        Citywide aggregated overview for the latest observation period.
        """
        if self._df is None or self._df.empty:
            return {
                "current_aqi": None,
                "category": "Unavailable",
                "color": "#6B7280",
                "health_advisory": "No observation data loaded.",
                "dominant_pollutant": None,
                "last_updated": None,
                "pollutants": {},
                "total_active_stations": 0,
                "data_mode": self.get_mode().value,
                "data_status": self.get_data_status().value,
                "freshness": FreshnessStatus.UNAVAILABLE.value,
                "age_seconds": None,
                "is_synthetic": True,
                "eligible": False
            }

        latest_ts = self._df["timestamp"].max()
        df_latest = self._df[self._df["timestamp"] == latest_ts]

        mean_pm25 = round(float(df_latest["ground_pm25"].mean()), 1)
        mean_pm10 = round(float(df_latest["ground_pm10"].mean()), 1)
        mean_no2 = round(float(df_latest["ground_no2"].mean()), 1)
        mean_so2 = round(float(df_latest["ground_so2"].mean()), 1)
        mean_co = round(float(df_latest["ground_co"].mean()), 2)
        mean_o3 = round(float(df_latest["ground_o3"].mean()), 1)

        pollutants = {
            "PM2.5": mean_pm25,
            "PM10": mean_pm10,
            "NO2": mean_no2,
            "SO2": mean_so2,
            "CO": mean_co,
            "O3": mean_o3
        }

        aqi_res = calculate_cpcb_aqi(pollutants, strict_eligibility=True)
        freshness_status, age_sec = self.calculate_freshness(latest_ts.to_pydatetime())
        mode = self.get_mode()
        data_status = self.get_data_status()

        return {
            "current_aqi": aqi_res["aqi"],
            "category": aqi_res["category"],
            "color": aqi_res["color"],
            "health_advisory": aqi_res["health_advisory"],
            "dominant_pollutant": aqi_res["dominant_pollutant"],
            "last_updated": latest_ts.isoformat(),
            "pollutants": pollutants,
            "sub_indices": aqi_res["sub_indices"],
            "total_active_stations": len(df_latest),
            "data_mode": mode.value,
            "data_status": data_status.value,
            "freshness": freshness_status.value,
            "age_seconds": round(age_sec, 1),
            "is_synthetic": mode == DataSourceMode.DEMO,
            "eligible": aqi_res["eligible"],
            "eligibility_reason": aqi_res.get("eligibility_reason")
        }

    def get_stations(self) -> List[Dict[str, Any]]:
        """
        List all stations with their latest observations and AQI calculations.
        """
        if self._df is None or self._df.empty:
            return []

        latest_ts = self._df["timestamp"].max()
        df_latest = self._df[self._df["timestamp"] == latest_ts]

        mode = self.get_mode()
        data_status = self.get_data_status()
        freshness_status, age_sec = self.calculate_freshness(latest_ts.to_pydatetime())

        stations_list = []
        for _, row in df_latest.iterrows():
            p_dict = {
                "PM2.5": float(row["ground_pm25"]),
                "PM10": float(row["ground_pm10"]),
                "NO2": float(row["ground_no2"]),
                "SO2": float(row["ground_so2"]),
                "CO": float(row["ground_co"]),
                "O3": float(row["ground_o3"])
            }
            aqi_res = calculate_cpcb_aqi(p_dict, strict_eligibility=True)

            stations_list.append({
                "id": str(row["station_id"]),
                "name": str(row["station_name"]),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "zone_type": str(row["zone_type"]),
                "current_pm25": float(row["ground_pm25"]),
                "current_aqi": aqi_res["aqi"],
                "category": aqi_res["category"],
                "color": aqi_res["color"],
                "dominant_pollutant": aqi_res["dominant_pollutant"],
                "last_updated": latest_ts.isoformat(),
                "freshness": freshness_status.value,
                "age_seconds": round(age_sec, 1),
                "data_status": data_status.value
            })

        return stations_list

    def get_station_detail(self, station_id: str) -> Optional[Dict[str, Any]]:
        if self._df is None or self._df.empty:
            return None

        df_st = self._df[self._df["station_id"] == station_id]
        if df_st.empty:
            return None

        latest_row = df_st.iloc[-1]
        latest_ts = latest_row["timestamp"]

        p_dict = {
            "PM2.5": float(latest_row["ground_pm25"]),
            "PM10": float(latest_row["ground_pm10"]),
            "NO2": float(latest_row["ground_no2"]),
            "SO2": float(latest_row["ground_so2"]),
            "CO": float(latest_row["ground_co"]),
            "O3": float(latest_row["ground_o3"])
        }
        aqi_res = calculate_cpcb_aqi(p_dict, strict_eligibility=True)
        freshness_status, age_sec = self.calculate_freshness(latest_ts.to_pydatetime())

        return {
            "id": station_id,
            "name": str(latest_row["station_name"]),
            "latitude": float(latest_row["latitude"]),
            "longitude": float(latest_row["longitude"]),
            "zone_type": str(latest_row["zone_type"]),
            "aqi_summary": aqi_res,
            "pollutant_readings": p_dict,
            "meteorological_conditions": {
                "temperature": float(latest_row["temperature"]),
                "humidity": float(latest_row["relative_humidity"]),
                "wind_speed": float(latest_row["wind_speed"]),
                "wind_direction": float(latest_row["wind_direction"]),
                "surface_pressure": float(latest_row["surface_pressure"]),
                "boundary_layer_height": float(latest_row["boundary_layer_height"])
            },
            "satellite_context": {
                "satellite_no2_column": float(latest_row["satellite_no2"]),
                "satellite_so2_column": float(latest_row["satellite_so2"]),
                "aerosol_index": float(latest_row["aerosol_index"]),
                "note": "Contextual tropospheric column density (OFFL L3); not surface concentration."
            },
            "last_updated": latest_ts.isoformat(),
            "freshness": freshness_status.value,
            "age_seconds": round(age_sec, 1),
            "data_status": self.get_data_status().value
        }

    def get_history(
        self,
        days: int = 30,
        station_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if self._df is None or self._df.empty:
            return {"days": days, "records": []}

        df = self._df.copy()
        if station_id and station_id != "all":
            df = df[df["station_id"] == station_id]

        max_date = df["timestamp"].max()
        start_date = max_date - pd.Timedelta(days=days)
        df_filtered = df[df["timestamp"] >= start_date]

        grouped = df_filtered.groupby("timestamp").agg({
            "ground_pm25": "mean",
            "ground_pm10": "mean",
            "ground_no2": "mean",
            "ground_so2": "mean",
            "temperature": "mean",
            "relative_humidity": "mean",
            "wind_speed": "mean",
            "satellite_no2": "mean",
            "aerosol_index": "mean"
        }).reset_index()

        history_records = []
        for _, row in grouped.iterrows():
            p_dict = {
                "PM2.5": round(float(row["ground_pm25"]), 1),
                "PM10": round(float(row["ground_pm10"]), 1),
                "NO2": round(float(row["ground_no2"]), 1),
                "SO2": round(float(row["ground_so2"]), 1)
            }
            aqi_res = calculate_cpcb_aqi(p_dict, strict_eligibility=True)

            history_records.append({
                "timestamp": row["timestamp"].strftime("%Y-%m-%d"),
                "pm25": p_dict["PM2.5"],
                "pm10": p_dict["PM10"],
                "no2": p_dict["NO2"],
                "so2": p_dict["SO2"],
                "aqi": aqi_res["aqi"],
                "category": aqi_res["category"],
                "color": aqi_res["color"],
                "temperature": round(float(row["temperature"]), 1),
                "humidity": round(float(row["relative_humidity"]), 1),
                "wind_speed": round(float(row["wind_speed"]), 1),
                "satellite_no2": float(row["satellite_no2"]),
                "aerosol_index": float(row["aerosol_index"])
            })

        return {
            "days": days,
            "station_id": station_id or "all_stations_avg",
            "total_records": len(history_records),
            "data_mode": self.get_mode().value,
            "data_status": self.get_data_status().value,
            "history": history_records
        }
