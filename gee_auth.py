"""
gee_auth.py

Handles Google Earth Engine authentication/initialization (FR-01).

Usage:
    from gee_auth import initialize_ee
    initialize_ee(project="your-gcp-project-id")

The first time this runs in a new environment it will open a browser
(or print a URL, in headless/Colab contexts) for you to authenticate.
After that, credentials are cached locally and `ee.Initialize()` is
enough on subsequent runs.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def initialize_ee(project: str | None = None) -> None:
    """Authenticate and initialize the Earth Engine API.

    Args:
        project: Your Google Cloud project ID registered for Earth Engine
            access. Required by current EE API versions.

    Raises:
        RuntimeError: if the `earthengine-api` package isn't installed, or
            if initialization fails after an authentication attempt.
    """
    try:
        import ee
    except ImportError as exc:
        raise RuntimeError(
            "The 'earthengine-api' package is not installed. "
            "Install it with: pip install earthengine-api"
        ) from exc

    try:
        ee.Initialize(project=project)
        logger.info("Earth Engine initialized (existing credentials).")
        return
    except Exception:
        logger.info("No valid cached credentials found — starting authentication.")

    ee.Authenticate()
    ee.Initialize(project=project)
    logger.info("Earth Engine authenticated and initialized.")
