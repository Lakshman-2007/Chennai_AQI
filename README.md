# Sentinel-5P Chennai Data Collection Pipeline (v0.1 MVP)

Implements the PRD: pulls Sentinel-5P/TROPOMI tropospheric data over
Chennai from Google Earth Engine and exports a validated, reproducible
CSV + metadata JSON. Does **not** compute AQI (out of scope for this
phase, per PRD section 22).

## What's wired up

- **Variable:** NO2 (`COPERNICUS/S5P/OFFL/L3_NO2`, band
  `tropospheric_NO2_column_number_density`, unit mol/m^2). This is the
  only pollutant verified against the live GEE catalog so far — CO, SO2,
  O3, CH4, HCHO, AER_AI are listed in `config.py`'s registry as
  placeholders and are deliberately blocked until someone verifies their
  collection ID / band / QA threshold (PRD section 23).
- **Region:** Chennai bounding box by default; set `region.method:
  boundary` + `region.boundary_source` in the config to use a real
  administrative polygon instead.
- **Quality filtering:** `qa_value > 0.75` for the NO2 tropospheric band
  (the threshold the EE catalog docs recommend for that specific band —
  stricter than the 0.50 used for most other S5P products).
- **Missing data:** any date with zero valid pixels is written as an
  empty CSV value (null), never 0.
- **Validation:** duplicate-date, pixel-count, NaN/Inf, and outlier
  checks run before export; a failed validation blocks the CSV from being
  written.

## Setup

```bash
pip install -r requirements.txt
```

You need a Google Cloud project with the Earth Engine API enabled and a
Google account registered for Earth Engine access
(https://code.earthengine.google.com/register).

## Run

```bash
python main.py --config config/chennai.yaml --gee-project YOUR_GCP_PROJECT_ID
```

First run will prompt an Earth Engine authentication flow (opens a
browser, or prints a URL/code in headless environments like Colab).
Credentials are cached after that.

Output:
```
output/sentinel5p_chennai.csv
output/sentinel5p_chennai_metadata.json
```

## Known limitation of this build

This code was generated without live network/GEE access, so it hasn't
been run end-to-end against the real Earth Engine API — only unit-level
logic (config loading, registry lookups, guardrails) was tested. Before
trusting the output:

1. Run it once on a short date range (a week) and manually sanity-check
   a few rows against the GEE Code Editor, per PRD section 13's
   recommended workflow.
2. Confirm `region.method: boundary` works if you switch to it — it
   expects a GeoJSON Feature/FeatureCollection/geometry on disk.

## Next steps (per PRD, do not start until the above is validated)

- Add verified registry entries for the remaining pollutants.
- Integrate ground monitoring stations, weather, and traffic data.
- Build the ML layer that turns these atmospheric columns + ground truth
  into an actual Chennai AQI estimate.
