# Prototype Dashboard — Live Snapshot AQI Calculator

Self-contained, interactive HTML dashboard. Open `index.html` directly
in any browser — no build step, no server, no dependencies.

## What it does
- Loads with the **actual real Chennai AQI reading** at the time this
  was built (pulled from CPCB via aqicn.org): overall AQI 76,
  PM2.5 76, PM10 48, NO2 5, SO2 2, O3 12, CO 10.
- Every value is **editable** — change any number and the per-pollutant
  category, the overall AQI, which pollutant is driving it, and the bar
  chart all recompute instantly using the real AQI breakpoint scale
  (0-50 Good, 51-100 Moderate, 101-150 Unhealthy for Sensitive Groups,
  151-200 Unhealthy, 201-300 Very Unhealthy, 300+ Hazardous).
- Overall AQI = the **worst** sub-index, not an average — matches how
  AQI is officially reported, since that's the pollutant actually
  driving health risk that day.

## What's real vs. what isn't
- The starting numbers are a **real one-time snapshot**, not synthetic.
- It is **not** a live-refreshing feed — a static HTML file can't call
  outside APIs on its own. Reopening it later won't show later data;
  it'll show the same snapshot until someone re-fetches and re-embeds
  fresh numbers.
- This dashboard sits on top of, and is separate from, the satellite
  (Sentinel-5P/TROPOMI) NO2 pipeline in the rest of this repo. It uses
  ground-station AQI data (aqicn/CPCB), not the satellite column-density
  pipeline's output — those are two different data sources, not yet
  connected to each other.

## Making it truly live
To get real auto-refresh, this needs to move off a static file onto
something with a backend: e.g. a small script that calls the aqicn.org
API (free token at aqicn.org/data-platform/token) on a schedule and
either writes to a page a server re-generates, or a page hosted
somewhere that permits outbound API calls. That's a separate,
slightly bigger build than this file.
