"""
collection.py

Loads the configured Sentinel-5P ImageCollection, validates it exists and
has imagery for the requested date range/region (FR-02, FR-03, FR-04, FR-05).
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

logger = logging.getLogger(__name__)


def load_collection(
    collection_id: str,
    band: str,
    qa_band: str,
    start_date: dt.date,
    end_date: dt.date,
    region: Any,
) -> Any:
    """Load, band-select, date-filter, and region-filter the S5P collection.

    Both the science band and the qa_band are kept (in that order) so that
    quality masking can happen before spatial reduction (see processing.py).

    Note on end_date semantics: ee.ImageCollection.filterDate's end bound is
    EXCLUSIVE. To make the pipeline's start/end behave inclusively (as a
    user configuring "2025-01-01" to "2025-01-31" would expect), we add one
    day to end_date before passing it to filterDate.
    """
    import ee

    collection = ee.ImageCollection(collection_id)

    # Validate both bands exist before doing anything else.
    first_image = collection.first()
    band_names = first_image.bandNames().getInfo()
    for required in (band, qa_band):
        if required not in band_names:
            raise ValueError(
                f"Band '{required}' not found in collection '{collection_id}'. "
                f"Available bands: {band_names}"
            )

    inclusive_end = end_date + dt.timedelta(days=1)
    filtered = (
        collection.select([band, qa_band])
        .filterDate(start_date.isoformat(), inclusive_end.isoformat())
        .filterBounds(region)
    )

    count = filtered.size().getInfo()
    if count == 0:
        raise ValueError(
            f"No imagery found for collection '{collection_id}', band "
            f"'{band}', date range {start_date}..{end_date}, over the "
            "configured region. Check the date range and region."
        )

    logger.info(
        "Loaded %d image(s) from %s [%s] between %s and %s",
        count, collection_id, band, start_date, end_date,
    )
    return filtered
