"""
quality.py

Applies Sentinel-5P quality filtering (PRD section 8, FR-06).

Quality filtering is mandatory unless explicitly disabled in config. Each
Sentinel-5P product ships its own qa_value band; we never assume a threshold
that wasn't looked up for the specific variable/band being used — that
threshold comes from config.DATASET_REGISTRY, not from this module.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def apply_quality_filter(
    image: Any,
    qa_band: str,
    qa_threshold: float,
    enabled: bool = True,
) -> Any:
    """Mask out low-quality pixels in a single S5P image.

    Args:
        image: an ee.Image that still carries its qa_band (select it before
            calling this if you also selected the science band — see
            processing.py for how both bands are carried through together).
        qa_band: name of the QA band, e.g. "qa_value".
        qa_threshold: minimum qa_value to keep (e.g. 0.75 for NO2 tropospheric).
        enabled: if False, returns the image unmodified (quality filtering
            skipped) — should only be used for debugging, per PRD section 8
            this is mandatory in production runs.
    """
    if not enabled:
        logger.warning("Quality filtering is DISABLED — results will include low-QA pixels.")
        return image

    qa = image.select(qa_band)
    mask = qa.gte(qa_threshold)
    return image.updateMask(mask)
