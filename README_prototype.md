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
- This version **calls a live API on every page load** —
  `api.waqi.info/feed/chennai`, sourced from CPCB — so the numbers you
  see are whatever Chennai's actual readings are at the moment you open
  it, not a frozen snapshot.
- Uses a free WAQI API token, visible in the page's JS source (it's a
  read-only public-data token, not a secret credential).
- If the live fetch fails (offline, API hiccup, token issue), the page
  falls back to the last known-good reading and says so on screen —
  it never just breaks silently.
- This dashboard sits on top of, and is separate from, the satellite
  (Sentinel-5P/TROPOMI) NO2 pipeline in the rest of this repo. It uses
  ground-station AQI data (aqicn/CPCB), not the satellite column-density
  pipeline's output — those are two different data sources, not yet
  connected to each other.
- **Important:** this only works when opened as a plain HTML file
  (double-click after downloading) or hosted somewhere like GitHub
  Pages. It will NOT fetch live data if viewed through a hosting
  environment that blocks outbound API calls (e.g. Claude's own
  published-artifact preview) — those show a fallback reading instead.
