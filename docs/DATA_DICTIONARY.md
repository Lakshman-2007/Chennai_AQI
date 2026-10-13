# Data Dictionary & Source Provenance Register

**Platform:** Chennai Air Quality Intelligence System  
**Version:** 2.1.0  
**Coordinate Reference System (CRS):** `EPSG:4326` (WGS84)  

---

## 1. Canonical Observation Schema

Every verified measurement and derived observation conforms to the following schema:

| Column / Field | Type | Description | Allowed Values / Range |
| :--- | :--- | :--- | :--- |
| `record_id` | String (UUID) | Globally unique normalized observation identifier | e.g. `c7b2a9f1-...` |
| `source_id` | String | Source adapter identifier | `cpcb_ground_monitoring`, `open_meteo_weather`, `sentinel5p_tropomi` |
| `source_record_id`| String (Nullable)| Original provider identifier for traceability | Provider key |
| `station_id` | String (Nullable)| Authoritative station identifier | `station_01` to `station_07` (null for gridded) |
| `station_name` | String (Nullable)| Authoritative name of monitoring station | e.g. `Alandur Bus Depot` |
| `latitude` | Float | Geographic latitude in WGS84 | $12.75^\circ\text{N} - 13.25^\circ\text{N}$ |
| `longitude` | Float | Geographic longitude in WGS84 | $80.05^\circ\text{E} - 80.35^\circ\text{E}$ |
| `observed_at` | Timestamp | Timezone-aware timestamp observation represents | ISO 8601 (UTC / Asia/Kolkata) |
| `retrieved_at` | Timestamp | Timestamp when system ingested record | ISO 8601 (UTC) |
| `pollutant` | Enum / String | Normalized pollutant designation | `PM2.5`, `PM10`, `NO2`, `SO2`, `CO`, `O3`, `NH3`, `PB` |
| `value` | Float (Nullable)| Measured concentration (never zero for missing) | Non-negative numeric |
| `unit` | String | Physical unit of concentration | `µg/m³` (gases/dust), `mg/m³` (CO) |
| `averaging_period`| String | Averaging window duration | `1h`, `8h`, `24h` |
| `quality_flag` | Enum | Quality verification flag | `valid`, `suspect`, `rejected`, `calibrated` |
| `data_status` | Enum | Physical provenance status | `observed`, `derived`, `estimated`, `forecast`, `synthetic`, `manual_import` |
| `raw_payload_ref` | String | Reference to raw payload or SHA-256 hash | SHA-256 hex string |

---

## 2. Multi-Source Register

### Source 1: Ground Continuous Monitoring Stations (CPCB / CAAQMS)
- **Provider:** Central Pollution Control Board (CPCB) & Tamil Nadu Pollution Control Board (TNPCB)
- **Monitors in Chennai:** 7 CAAQMS Stations:
  1. `station_01`: Alandur Bus Depot (Commercial / Transit)
  2. `station_02`: Manali Industrial Zone (Petrochemical / Refineries)
  3. `station_03`: Velachery Residential Area (IT Corridor)
  4. `station_04`: Kodungaiyur (Solid Waste / North Urban)
  5. `station_05`: Royapuram Coastal Zone (Port / Marine Urban)
  6. `station_06`: Arumbakkam Urban Center (High Traffic Hub)
  7. `station_07`: IIT Madras Campus (Institutional Canopy Reserve)
- **Monitored Variables:** PM2.5, PM10, NO2, SO2, CO, O3, NH3.

### Source 2: Surface Meteorological Observables (Open-Meteo)
- **Provider:** Open-Meteo Reanalysis & Forecast Engine (ECMWF IFS / DWD ICON models)
- **Variables:** Surface temperature ($^\circ\text{C}$), relative humidity ($\%$) at 2m, wind speed ($\text{km/h}$), wind direction ($^\circ$) at 10m, barometric pressure ($\text{hPa}$), planetary boundary layer height ($\text{m}$), precipitation accumulation ($\text{mm}$).

### Source 3: Sentinel-5P TROPOMI Remote Sensing
- **Provider:** ESA Copernicus Programme / Google Earth Engine
- **Products:** `COPERNICUS/S5P/OFFL/L3_NO2`, `COPERNICUS/S5P/OFFL/L3_SO2`, `COPERNICUS/S5P/OFFL/L3_CO`, `COPERNICUS/S5P/OFFL/L3_O3`, `COPERNICUS/S5P/OFFL/L3_AER_AI`
- **Units:** $\text{mol/m}^2$ (vertical column density) and dimensionless Aerosol Index.
- **Rule:** Offline contextual layer only in Release 1. Excluded from live operational forecast requirements.

### Source 4: Greater Chennai Corporation (GCC) Administrative GIS
- **Provider:** Greater Chennai Corporation GIS Portal
- **Layers:** 15 Administrative Zones (Zone 1 Thiruvottiyur through Zone 15 Sholinganallur).
- **CRS:** `EPSG:4326` (WGS84).

---

## 3. Freshness TTL State Machine (PRD 21.5)

- **Fresh:** $\text{Age} \le 2\text{ hours}$ from `observed_at`.
- **Stale:** $2\text{ hours} < \text{Age} \le 24\text{ hours}$.
- **Expired:** $\text{Age} > 24\text{ hours}$ (historical only; not presented as current condition).
