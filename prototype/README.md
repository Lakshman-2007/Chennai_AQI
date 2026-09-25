# Prototype Dashboard

A self-contained HTML dashboard previewing what the v0.1 pipeline's
output looks like: daily NO2 chart, region map, pollutant registry
status, and the pipeline flow.

**This uses synthetic data**, shaped exactly like the real CSV schema
in `export.py` (date, value, valid_pixel_count), because generating it
required a live, authenticated Earth Engine session that wasn't
available in the environment this was built in.

## Files
- `index.html` — the dashboard, open directly in any browser, no build step or server needed.
- `sample_data.json` — the synthetic Jan 2025 NO2 series used by the dashboard (31 days, ~10% missing to mirror real QA-filtered gaps).

## Swapping in real data
Once `main.py` has been run against live Earth Engine and produced
`output/sentinel5p_chennai.csv`, replace the `data` array in
`index.html` (search for `const data = `) with the real rows,
mapped to `{date, value, valid_pixel_count}` objects (`value: null`
for empty CSV cells).

## Known limitation
Not yet validated against a real pipeline run — see the main
README's "Known limitation of this build" section, which still
applies here.
