"""
main.py

Entry point. Run with:

    python main.py --config config/chennai.yaml

Prints progress matching PRD section 19, then writes:
    output/sentinel5p_chennai.csv
    output/sentinel5p_chennai_metadata.json

Requires:
    pip install earthengine-api pyyaml
    A Google Cloud project with the Earth Engine API enabled, and a GEE
    account authenticated via gee_auth.initialize_ee().
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from config import Config
from gee_auth import initialize_ee
from region import build_region
from collection import load_collection
from processing import aggregate_daily_observations
from export import write_csv, write_metadata
from validation import validate_observations

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("sentinel5p_pipeline")


def run(config_path: str, gee_project: str | None) -> int:
    cfg = Config.from_yaml(config_path)
    spec = cfg.dataset_spec()
    start_date, end_date = cfg.date.as_dates()
    qa_threshold = cfg.quality.threshold_override or spec["qa_threshold"]

    print("Loading Google Earth Engine...")
    initialize_ee(project=gee_project)

    print("Loading Sentinel-5P collection...")
    region_geom, region_definition = build_region(cfg.region)

    print("Filtering dates...")
    print("Filtering Chennai region...")
    filtered = load_collection(
        collection_id=spec["collection_id"],
        band=spec["band"],
        qa_band=spec["qa_band"],
        start_date=start_date,
        end_date=end_date,
        region=region_geom,
    )

    print("Applying quality filter...")
    print("Extracting measurements...")
    print("Aggregating daily values...")
    observations = aggregate_daily_observations(
        filtered_collection=filtered,
        region=region_geom,
        band=spec["band"],
        qa_band=spec["qa_band"],
        qa_threshold=qa_threshold,
        quality_enabled=cfg.quality.enabled,
        spatial_aggregation=cfg.processing.spatial_aggregation,
    )

    print("Validating dataset...")
    report = validate_observations(observations, variable=cfg.processing.variable)
    logger.info(report.summary())
    if not report.passed:
        print("\nVALIDATION FAILED — see issues above. CSV was not exported.")
        return 1

    print("Exporting CSV...")
    os.makedirs(cfg.output.output_dir, exist_ok=True)
    csv_path = os.path.join(cfg.output.output_dir, cfg.output.csv_filename)
    metadata_path = os.path.join(cfg.output.output_dir, cfg.output.metadata_filename)

    region_centroid = (
        (cfg.region.min_lat + cfg.region.max_lat) / 2,
        (cfg.region.min_lon + cfg.region.max_lon) / 2,
    )

    write_csv(
        observations,
        csv_path,
        region_name=cfg.region.name,
        region_centroid=region_centroid,
        variable=spec["band"],
        unit=spec["unit"],
        aggregation=cfg.processing.spatial_aggregation,
        dataset=spec["collection_id"],
        processing_version=cfg.output.processing_version,
    )
    write_metadata(
        metadata_path,
        collection_id=spec["collection_id"],
        band=spec["band"],
        unit=spec["unit"],
        start_date=cfg.date.start,
        end_date=cfg.date.end,
        region_name=cfg.region.name,
        region_definition=region_definition,
        aggregation_method=cfg.processing.spatial_aggregation,
        quality_enabled=cfg.quality.enabled,
        qa_band=spec["qa_band"],
        qa_threshold=qa_threshold,
        qa_reason=spec["qa_reason"],
        processing_version=cfg.output.processing_version,
    )

    print("\nSUCCESS\n")
    print(f"Output:\n{csv_path}\n{metadata_path}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentinel-5P Chennai data collection pipeline")
    parser.add_argument("--config", default="config/chennai.yaml", help="Path to YAML config")
    parser.add_argument("--gee-project", default=None, help="GCP project ID registered for Earth Engine")
    args = parser.parse_args()

    sys.exit(run(args.config, args.gee_project))
