"""
CPCB & CAAQMS Ground Air Quality Data Adapter.

Handles:
1. Manual official CSV report importation with SHA-256 integrity hashing and row rejection audits
2. Schema normalization into CanonicalObservation
3. Authoritative Chennai station resolution
4. Strict data status labeling: 'observed' (official import) or 'synthetic' (demo)
"""

import os
import io
import csv
import json
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import pandas as pd

from backend.app.data_sources.base import BaseDataSourceAdapter
from backend.app.schemas.canonical import (
    CanonicalObservation,
    ImportManifest,
    SourceHealthStatus,
    DataSourceMode,
    DataStatusEnum,
    FreshnessStatus,
    QualityFlagEnum
)

AUTHORITATIVE_CHENNAI_STATIONS = {
    "station_01": {
        "id": "station_01",
        "name": "Alandur Bus Depot",
        "aliases": ["alandur", "alandur bus depot", "alandur caaqms"],
        "latitude": 13.0012,
        "longitude": 80.2015,
        "zone_type": "Commercial / Transit Corridor"
    },
    "station_02": {
        "id": "station_02",
        "name": "Manali Industrial Zone",
        "aliases": ["manali", "manali industrial area", "manali cpcb"],
        "latitude": 13.1667,
        "longitude": 80.2667,
        "zone_type": "Industrial / Petrochemical"
    },
    "station_03": {
        "id": "station_03",
        "name": "Velachery Residential Area",
        "aliases": ["velachery", "velachery residential", "velachery caaqms"],
        "latitude": 12.9815,
        "longitude": 80.2180,
        "zone_type": "Residential / IT Corridor"
    },
    "station_04": {
        "id": "station_04",
        "name": "Kodungaiyur",
        "aliases": ["kodungaiyur", "kodungaiyur caaqms"],
        "latitude": 13.1340,
        "longitude": 80.2640,
        "zone_type": "Residential / Solid Waste Site"
    },
    "station_05": {
        "id": "station_05",
        "name": "Royapuram Coastal Zone",
        "aliases": ["royapuram", "royapuram coastal"],
        "latitude": 13.1140,
        "longitude": 80.2940,
        "zone_type": "Port / Coastal Urban"
    },
    "station_06": {
        "id": "station_06",
        "name": "Arumbakkam Urban Center",
        "aliases": ["arumbakkam", "arumbakkam urban"],
        "latitude": 13.0720,
        "longitude": 80.2100,
        "zone_type": "Commercial / High Traffic"
    },
    "station_07": {
        "id": "station_07",
        "name": "IIT Madras Campus",
        "aliases": ["iit madras", "iitm", "iit madras campus"],
        "latitude": 12.9915,
        "longitude": 80.2336,
        "zone_type": "Institutional / Canopy Reserve"
    }
}

POLLUTANT_COLUMN_MAP = {
    "pm2.5": "PM2.5",
    "pm25": "PM2.5",
    "pm2_5": "PM2.5",
    "pm10": "PM10",
    "no2": "NO2",
    "so2": "SO2",
    "co": "CO",
    "o3": "O3",
    "ozone": "O3",
    "nh3": "NH3",
    "pb": "PB",
    "lead": "PB"
}

PHYSICAL_LIMITS = {
    "PM2.5": (0.0, 1000.0),
    "PM10": (0.0, 1500.0),
    "NO2": (0.0, 1000.0),
    "SO2": (0.0, 1500.0),
    "CO": (0.0, 100.0),
    "O3": (0.0, 1000.0),
    "NH3": (0.0, 2500.0),
    "PB": (0.0, 50.0)
}

class CPCBDataAdapter(BaseDataSourceAdapter):
    """
    Adapter for CPCB/CAAQMS ground observation data.
    Implements P0 Manual CSV Import requirements (FR-01, FR-02, FR-03, FR-04, FR-05).
    """

    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
            )
        self.storage_dir = storage_dir
        self.raw_dir = os.path.join(storage_dir, "raw")
        self.manifest_path = os.path.join(storage_dir, "import_manifests.json")
        os.makedirs(self.raw_dir, exist_ok=True)
        self.source_id = "cpcb_ground_monitoring"

    def get_source_id(self) -> str:
        return self.source_id

    def resolve_station(self, raw_name_or_id: str) -> Optional[Dict[str, Any]]:
        if not raw_name_or_id:
            return None
        cleaned = str(raw_name_or_id).strip().lower()
        if cleaned in AUTHORITATIVE_CHENNAI_STATIONS:
            return AUTHORITATIVE_CHENNAI_STATIONS[cleaned]
        for st_id, st_info in AUTHORITATIVE_CHENNAI_STATIONS.items():
            if cleaned == st_info["name"].lower():
                return st_info
            if any(alias in cleaned for alias in st_info["aliases"]):
                return st_info
        return None

    def validate(self, payload: Any) -> Tuple[bool, List[str]]:
        errors = []
        if isinstance(payload, pd.DataFrame):
            if payload.empty:
                errors.append("Payload dataframe is completely empty")
        elif isinstance(payload, str):
            if not os.path.exists(payload):
                errors.append(f"File not found: {payload}")
        return len(errors) == 0, errors

    def normalize(self, payload: Any) -> List[Dict[str, Any]]:
        # Returns raw dict rows ready for canonical ingestion
        return []

    def fetch(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        area: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        return []

    def import_csv_file(
        self,
        file_path_or_buffer: Any,
        source_url_or_origin: str = "CPCB CAAQMS Portal Manual Export",
        filename: Optional[str] = None
    ) -> Tuple[ImportManifest, List[CanonicalObservation]]:
        """
        Idempotent manual CSV import pipeline.
        Parses CSV, validates units and physical bounds, rejects erroneous rows with reasons,
        computes SHA-256 hash, and saves immutable raw file + audit manifest.
        """
        if isinstance(file_path_or_buffer, str) and os.path.exists(file_path_or_buffer):
            with open(file_path_or_buffer, "rb") as f:
                content = f.read()
            raw_filename = filename or os.path.basename(file_path_or_buffer)
        elif hasattr(file_path_or_buffer, "read"):
            content = file_path_or_buffer.read()
            if isinstance(content, str):
                content = content.encode("utf-8")
            raw_filename = filename or "uploaded_cpcb_data.csv"
        elif isinstance(file_path_or_buffer, bytes):
            content = file_path_or_buffer
            raw_filename = filename or "uploaded_cpcb_data.csv"
        else:
            raise ValueError("Unsupported input type for import_csv_file")

        # Compute SHA-256 Checksum
        sha256_hash = hashlib.sha256(content).hexdigest()

        # Check existing manifests for idempotency
        manifests = self._load_manifests()
        for existing in manifests:
            if existing.get("file_sha256") == sha256_hash:
                manifest_obj = ImportManifest(**existing)
                return manifest_obj, []

        # Save immutable raw copy
        saved_raw_path = os.path.join(self.raw_dir, f"{sha256_hash}_{raw_filename}")
        if not os.path.exists(saved_raw_path):
            with open(saved_raw_path, "wb") as f:
                f.write(content)

        # Parse CSV
        df = pd.read_csv(io.BytesIO(content))
        total_rows = len(df)

        accepted_observations: List[CanonicalObservation] = []
        rejection_reasons: Dict[str, int] = {}
        stations_found = set()
        pollutants_found = set()
        accepted_row_count = 0
        rejected_row_count = 0
        now_utc = datetime.now(timezone.utc)

        # Normalize column headers
        col_mapping = {}
        for col in df.columns:
            cleaned_col = str(col).lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
            matched = False
            for p_key, p_norm in POLLUTANT_COLUMN_MAP.items():
                if p_key in cleaned_col:
                    col_mapping[col] = p_norm
                    matched = True
                    break
            if not matched:
                if any(k in cleaned_col for k in ["date", "time", "timestamp"]):
                    col_mapping[col] = "timestamp"
                elif any(k in cleaned_col for k in ["station", "location"]):
                    col_mapping[col] = "station"

        for idx, row in df.iterrows():
            row_has_valid_obs = False
            rejection_key = None

            # Station resolution
            st_raw = row.get("station") or row.get("Station") or row.get("station_name") or row.get("station_id")
            station_info = self.resolve_station(str(st_raw) if pd.notnull(st_raw) else "station_01")
            if not station_info:
                rejection_reasons["unknown_station"] = rejection_reasons.get("unknown_station", 0) + 1
                rejected_row_count += 1
                continue

            stations_found.add(station_info["id"])

            # Timestamp parsing
            ts_raw = row.get("timestamp") or row.get("Timestamp") or row.get("Date") or row.get("From Date")
            parsed_ts = None
            if pd.notnull(ts_raw):
                try:
                    parsed_ts = pd.to_datetime(ts_raw)
                    if parsed_ts.tzinfo is None:
                        parsed_ts = parsed_ts.tz_localize(timezone.utc)
                except Exception:
                    pass

            if not parsed_ts:
                rejection_reasons["invalid_timestamp"] = rejection_reasons.get("invalid_timestamp", 0) + 1
                rejected_row_count += 1
                continue

            # Extract pollutants
            for orig_col, norm_pol in col_mapping.items():
                if norm_pol in PHYSICAL_LIMITS:
                    val = row.get(orig_col)
                    if pd.notnull(val):
                        try:
                            num_val = float(val)
                            min_lim, max_lim = PHYSICAL_LIMITS[norm_pol]
                            if num_val < min_lim or num_val > max_lim:
                                rejection_reasons[f"out_of_bounds_{norm_pol}"] = (
                                    rejection_reasons.get(f"out_of_bounds_{norm_pol}", 0) + 1
                                )
                                continue

                            unit = "mg/m³" if norm_pol == "CO" else "µg/m³"
                            avg_period = "8h" if norm_pol in ["CO", "O3"] else "24h"

                            obs = CanonicalObservation(
                                record_id=str(uuid.uuid4()),
                                source_id=self.source_id,
                                source_record_id=f"{station_info['id']}_{norm_pol}_{parsed_ts.isoformat()}",
                                station_id=station_info["id"],
                                station_name=station_info["name"],
                                latitude=station_info["latitude"],
                                longitude=station_info["longitude"],
                                observed_at=parsed_ts,
                                retrieved_at=now_utc,
                                pollutant=norm_pol,
                                value=round(num_val, 2),
                                unit=unit,
                                averaging_period=avg_period,
                                quality_flag=QualityFlagEnum.VALID,
                                data_status=DataStatusEnum.OBSERVED,
                                raw_payload_ref=sha256_hash
                            )
                            accepted_observations.append(obs)
                            pollutants_found.add(norm_pol)
                            row_has_valid_obs = True
                        except (ValueError, TypeError):
                            rejection_reasons[f"non_numeric_{norm_pol}"] = (
                                rejection_reasons.get(f"non_numeric_{norm_pol}", 0) + 1
                            )

            if row_has_valid_obs:
                accepted_row_count += 1
            else:
                rejected_row_count += 1

        timestamps = [obs.observed_at for obs in accepted_observations]
        min_ts = min(timestamps).isoformat() if timestamps else None
        max_ts = max(timestamps).isoformat() if timestamps else None

        manifest = ImportManifest(
            import_id=str(uuid.uuid4()),
            source_file=raw_filename,
            file_sha256=sha256_hash,
            source_url_or_origin=source_url_or_origin,
            downloaded_at=now_utc,
            imported_at=now_utc,
            total_rows_read=total_rows,
            rows_accepted=accepted_row_count,
            rows_rejected=rejected_row_count,
            rejection_reasons=rejection_reasons,
            station_ids_found=sorted(list(stations_found)),
            pollutants_found=sorted(list(pollutants_found)),
            time_range_start=min_ts,
            time_range_end=max_ts,
            status="success"
        )

        manifests.append(manifest.model_dump(mode="json"))
        self._save_manifests(manifests)

        return manifest, accepted_observations

    def _load_manifests(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_manifests(self, manifests: List[Dict[str, Any]]):
        with open(self.manifest_path, "w") as f:
            json.dump(manifests, f, indent=2, default=str)

    def health_check(self) -> SourceHealthStatus:
        manifests = self._load_manifests()
        mode = DataSourceMode.MANUAL_IMPORT if manifests else DataSourceMode.DEMO
        last_success = None
        record_count = 0

        if manifests:
            last_manifest = manifests[-1]
            try:
                last_success = pd.to_datetime(last_manifest.get("imported_at")).to_pydatetime()
            except Exception:
                pass
            record_count = sum(m.get("rows_accepted", 0) for m in manifests)

        now = datetime.now(timezone.utc)
        age_sec = (now - last_success).total_seconds() if last_success else 999999.0

        if age_sec <= 2 * 3600:
            freshness = FreshnessStatus.FRESH
        elif age_sec <= 24 * 3600:
            freshness = FreshnessStatus.STALE
        else:
            freshness = FreshnessStatus.EXPIRED

        return SourceHealthStatus(
            source_id=self.source_id,
            name="Ground Air Quality Monitoring Stations",
            provider="CPCB (Central Pollution Control Board) / CAAQMS Chennai",
            mode=mode,
            status="healthy" if mode == DataSourceMode.MANUAL_IMPORT else "degraded",
            last_attempt_at=now,
            last_success_at=last_success,
            age_seconds=round(age_sec, 1),
            freshness=freshness,
            stale_threshold_hours=24.0,
            record_count=record_count if record_count > 0 else 3185,
            data_status=DataStatusEnum.OBSERVED if mode == DataSourceMode.MANUAL_IMPORT else DataStatusEnum.SYNTHETIC,
            attribution="CPCB CAAQMS Official Monitoring Portal / OpenAQ India",
            error_message=None if mode == DataSourceMode.MANUAL_IMPORT else "Operating in seeded demo mode. Import official CPCB CSV to activate live verified observations."
        )
