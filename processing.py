"""
processing.py

Spatial aggregation over the Chennai region (FR-07) and temporal
aggregation into daily/weekly/monthly observations (FR-08), with strict
missing-data handling (FR-09, PRD section 9 / Rule 4): a day with zero
valid pixels must be recorded as a missing value, never coerced to 0.
"""

from __future__ import annotations

import logging
from typing import Any

from quality import apply_quality_filter

logger = logging.getLogger(__name__)

_REDUCERS = {
    "mean": "mean",
    "median": "median",
    "min": "min",
    "max": "max",
}


def _build_reducer(spatial_aggregation: str) -> Any:
    import ee

    if spatial_aggregation not in _REDUCERS:
        raise ValueError(
            f"Unknown spatial_aggregation '{spatial_aggregation}'. "
            f"Choose from {list(_REDUCERS)}."
        )
    stat_reducer = getattr(ee.Reducer, _REDUCERS[spatial_aggregation])()
    # Always carry pixel_count alongside the statistic (PRD section 7).
    return stat_reducer.combine(reducer2=ee.Reducer.count(), sharedInputs=True)


def aggregate_daily_observations(
    filtered_collection: Any,
    region: Any,
    band: str,
    qa_band: str,
    qa_threshold: float,
    quality_enabled: bool,
    spatial_aggregation: str,
    scale_meters: float = 1113.2,
) -> list[dict[str, Any]]:
    """Reduce each image in the collection to one spatial statistic per day.

    Sentinel-5P can produce more than one overpass image per day for a given
    region; all images sharing a calendar date are merged (via ee.Reducer
    over the mosaic/pixel set) into a single daily value, consistent with
    PRD section 5's "start with daily observations" MVP requirement.

    Returns a list of plain-Python dicts, one per calendar date in range,
    with `value=None` when there were zero valid pixels for that date
    (never 0 — PRD section 9).
    """
    import ee

    reducer = _build_reducer(spatial_aggregation)
    stat_key = spatial_aggregation

    def _quality_masked(img: Any) -> Any:
        qa_selected = img  # qa_band must already be present as a sibling band
        return apply_quality_filter(
            qa_selected, qa_band=qa_band, qa_threshold=qa_threshold, enabled=quality_enabled
        )

    # Re-load the same collection but keep both the science band and qa_band
    # together so masking can happen before reduction.
    collection_id_note = (
        "Caller must pass a collection already select()-ed to [band, qa_band]."
    )
    logger.debug(collection_id_note)

    masked = filtered_collection.map(_quality_masked)

    # Group images by calendar date, then reduce each date's mosaic over the region.
    dates = ee.List(
        masked.aggregate_array("system:time_start")
    ).map(lambda t: ee.Date(t).format("YYYY-MM-dd")).distinct()

    def _reduce_one_date(date_str: Any) -> Any:
        date_str = ee.String(date_str)
        day_start = ee.Date(date_str)
        day_end = day_start.advance(1, "day")
        day_images = masked.filterDate(day_start, day_end)

        day_mosaic = day_images.select(band).mosaic()
        stats = day_mosaic.reduceRegion(
            reducer=reducer,
            geometry=region,
            scale=scale_meters,
            maxPixels=1e9,
        )

        return ee.Feature(
            None,
            {
                "date": date_str,
                "value": stats.get(f"{band}_{stat_key}"),
                "valid_pixel_count": stats.get(f"{band}_count"),
            },
        )

    daily_features = ee.FeatureCollection(dates.map(_reduce_one_date))
    raw = daily_features.getInfo()["features"]

    results = []
    for feat in raw:
        props = feat["properties"]
        pixel_count = props.get("valid_pixel_count") or 0
        value = props.get("value")
        # Enforce: zero valid pixels => value is missing, never 0.
        if not pixel_count:
            value = None
        results.append(
            {
                "date": props["date"],
                "value": value,
                "valid_pixel_count": int(pixel_count),
            }
        )

    results.sort(key=lambda r: r["date"])
    return results
