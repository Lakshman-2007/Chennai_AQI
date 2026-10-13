# CPCB National Air Quality Index (NAQI) Technical Methodology

**System Standard Version:** `CPCB-NAQI-2014-v1.0`  
**Reference Document:** Central Pollution Control Board (CPCB), Ministry of Environment, Forest & Climate Change, Government of India: *National Air Quality Index* Technical Report.  
**Official Reference URLs:**
- [CPCB National AQI Report](https://airquality.cpcb.gov.in/ccr_docs/FINAL-REPORT_AQI_.pdf)
- [CPCB Technical Documentation Portal](https://www.cpcb.gov.in/displaypdf.php?id=bmF0aW9uYWwtYWlyLXF1YWxpdHktaW5kZXgvRklOQUwtUkVQT1JUX0FRSV8ucGRm)

---

## 1. Mathematical Formulation

Sub-index for each monitored pollutant is computed via piecewise linear interpolation across official breakpoint concentration intervals:

$$I_p = \frac{I_{Hi} - I_{Lo}}{B_{Hi} - B_{Lo}} \times (C_p - B_{Lo}) + I_{Lo}$$

Where:
- $C_p$: Concentration of pollutant $p$
- $B_{Hi}$: Breakpoint concentration that is greater than or equal to $C_p$
- $B_{Lo}$: Breakpoint concentration that is less than or equal to $C_p$
- $I_{Hi}$: Sub-index value corresponding to $B_{Hi}$
- $I_{Lo}$: Sub-index value corresponding to $B_{Lo}$
- $I_p$: Computed sub-index for pollutant $p$

---

## 2. Official Breakpoint Concentration Tables

All concentrations are expressed in $\mu\text{g/m}^3$ except Carbon Monoxide (CO), which is expressed in $\text{mg/m}^3$.

| AQI Category | Sub-Index Range | PM2.5 (24h) | PM10 (24h) | NO2 (24h) | SO2 (24h) | CO (8h, mg/m³) | O3 (8h) | NH3 (24h) | Pb (24h) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Good** | 0 – 50 | 0 – 30 | 0 – 50 | 0 – 40 | 0 – 40 | 0.0 – 1.0 | 0 – 50 | 0 – 200 | 0.0 – 0.5 |
| **Satisfactory** | 51 – 100 | 31 – 60 | 51 – 100 | 41 – 80 | 41 – 80 | 1.1 – 2.0 | 51 – 100 | 201 – 400 | 0.6 – 1.0 |
| **Moderate** | 101 – 200 | 61 – 90 | 101 – 250 | 81 – 180 | 81 – 380 | 2.1 – 10.0 | 101 – 168 | 401 – 800 | 1.1 – 2.0 |
| **Poor** | 201 – 300 | 91 – 120 | 251 – 350 | 181 – 280 | 381 – 800 | 10.1 – 17.0 | 169 – 208 | 801 – 1200 | 2.1 – 3.0 |
| **Very Poor** | 301 – 400 | 121 – 250 | 351 – 430 | 281 – 400 | 801 – 1600 | 17.1 – 34.0 | 209 – 748 | 1201 – 1800 | 3.1 – 3.5 |
| **Severe** | 401 – 500 | 250+ | 430+ | 400+ | 1600+ | 34.0+ | 748+ | 1800+ | 3.5+ |

---

## 3. Strict CPCB Minimum Eligibility Criteria

Under the official CPCB regulation enforced in this platform:
1. **Minimum Pollutant Sufficiency:** An overall AQI can **only** be calculated if data for **at least 3 pollutants** are available.
2. **Particulate Matter Mandate:** Among the available monitored pollutants, **at least one MUST be a particulate matter indicator** ($\text{PM}_{2.5}$ or $\text{PM}_{10}$).
3. **No Imputation to Zero:** Missing pollutant observations must **never** be imputed to $0.0$. Incomplete observations return an explicit status:
   $$\text{status} = \text{Insufficient Data / Ineligible}$$
4. **Overall AQI Determination:**
   $$\text{AQI} = \max(I_{\text{PM2.5}}, I_{\text{PM10}}, I_{\text{NO2}}, I_{\text{SO2}}, I_{\text{CO}}, I_{\text{O3}}, I_{\text{NH3}}, I_{\text{Pb}})$$
   The dominant pollutant is defined as the pollutant corresponding to the maximum sub-index. If tied, deterministic priority order ($\text{PM}_{2.5} > \text{PM}_{10} > \text{NO}_2 > \text{SO}_2 > \dots$) is enforced.

---

## 4. Averaging Completeness Rules

- **24-hour Averaging (PM2.5, PM10, NO2, SO2, NH3, Pb):** Minimum **16 valid hours** ($\ge 66.7\%$) required.
- **8-hour Averaging (CO, O3):** Minimum **6 valid hours** ($\ge 75.0\%$) required.
