# NRW Ozone Forecast

Daily 3-day ground-level ozone forecast for all municipalities in North Rhine-Westphalia (NRW), Germany.  
Data source: [CAMS European Air Quality Forecasts](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts) — ensemble model, surface level (0 m).

---

<!-- TOP10_START -->

## Top 10 — Highest Ozone Values Today (2026-05-27)

*Forecast base: 2026-05-27 00:00 UTC · Generated: 2026-05-27T09:48:08Z*

|   | Municipality | Peak time (UTC) | O₃ (µg/m³) |
|:---:|:---|:---|---:|
| ![](https://placehold.co/16x16/FAE88E/FAE88E.png) | **Erftstadt** | 2026-05-27 15:00 UTC | **119.1** |
| ![](https://placehold.co/16x16/FAE88E/FAE88E.png) | **Hürth** | 2026-05-27 15:00 UTC | **119.1** |
| ![](https://placehold.co/16x16/FAE88E/FAE88E.png) | **Euskirchen** | 2026-05-27 16:00 UTC | **118.5** |
| ![](https://placehold.co/16x16/FAE88E/FAE88E.png) | **Swisttal** | 2026-05-27 16:00 UTC | **118.4** |
| ![](https://placehold.co/16x16/FAE88E/FAE88E.png) | **Weilerswist** | 2026-05-27 15:00 UTC | **116.6** |
| ![](https://placehold.co/16x16/FAE88E/FAE88E.png) | **Rheinbach** | 2026-05-27 15:00 UTC | **115.7** |
| ![](https://placehold.co/16x16/FAE88E/FAE88E.png) | **Bornheim** | 2026-05-27 15:00 UTC | **114.9** |
| ![](https://placehold.co/16x16/FAE88E/FAE88E.png) | **Brühl** | 2026-05-27 14:00 UTC | **114.7** |
| ![](https://placehold.co/16x16/FAE88E/FAE88E.png) | **Wesseling** | 2026-05-27 14:00 UTC | **114.7** |
| ![](https://placehold.co/16x16/FAE88E/FAE88E.png) | **Dahlem** | 2026-05-27 11:00 UTC | **114.3** |

### Colour scale (µg/m³)

| Colour | Range |
|:---:|:---|
| ![](https://placehold.co/14x14/C6E9F3/C6E9F3.png) | 0–20 |
| ![](https://placehold.co/14x14/B3DFEB/B3DFEB.png) | 20–40 |
| ![](https://placehold.co/14x14/A0D5E3/A0D5E3.png) | 40–60 |
| ![](https://placehold.co/14x14/BFDFCD/BFDFCD.png) | 60–80 |
| ![](https://placehold.co/14x14/EBEEB3/EBEEB3.png) | 80–100 |
| ![](https://placehold.co/14x14/FAE88E/FAE88E.png) | 100–120 |
| ![](https://placehold.co/14x14/F5D362/F5D362.png) | 120–140 |
| ![](https://placehold.co/14x14/EDB43C/EDB43C.png) | 140–160 |
| ![](https://placehold.co/14x14/E18620/E18620.png) | 160–180 |
| ![](https://placehold.co/14x14/D05C0B/D05C0B.png) | 180–200 |
| ![](https://placehold.co/14x14/AA4110/AA4110.png) | 200–240 |
| ![](https://placehold.co/14x14/852615/852615.png) | 240–500 |
| ![](https://placehold.co/14x14/8526BA/8526BA.png) | > 500 |

<!-- TOP10_END -->

---

## What it does

A GitHub Actions workflow runs every morning at **06:00 UTC**. You can trigger a run at any time via **Actions → NRW Ozone Forecast → Run workflow**. It:

1. Downloads the CAMS 00:00 UTC ensemble ozone forecast (lead hours 0–96 h) for the NRW bounding box. 
2. Maps each municipality centroid to the nearest 11 × 11 km grid cell.
3. Finds the **daily peak ozone value** for today, tomorrow and the day after tomorrow.
4. Updates the Top-10 table in this README.
5. Writes the full results to `output/ozone_forecast_nrw.json` and pushes everything back to this repository.

---

## Output format

`output/ozone_forecast_nrw.json`

```json
{
  "generated_at_utc": "2026-03-26T06:12:34Z",
  "forecast_base_date": "2026-03-26",
  "data_source": "CAMS European Air Quality Forecasts (ensemble, level 0)",
  "unit": "µg/m³",
  "municipalities": [
    {
      "name": "Köln",
      "lat": 50.938107,
      "lon": 6.957068,
      "forecast": {
        "today": {
          "peak_ozone_ug_m3": 112.4,
          "peak_time_utc": "2026-03-26T13:00:00Z"
        },
        "tomorrow": {
          "peak_ozone_ug_m3": 98.7,
          "peak_time_utc": "2026-03-27T14:00:00Z"
        },
        "day_after_tomorrow": {
          "peak_ozone_ug_m3": 105.1,
          "peak_time_utc": "2026-03-28T12:00:00Z"
        }
      }
    }
  ]
}
```

---

## Repository structure

```
nrw-ozone-forecast/
├── .github/
│   └── workflows/
│       └── ozone_forecast.yml   ← GitHub Actions workflow
├── output/
│   ├── .gitkeep
│   └── ozone_forecast_nrw.json  ← updated daily (auto-committed)
├── municipality_nrw.csv         ← municipality centroids
├── run_forecast.py              ← main forecast script
├── update_readme.py             ← injects Top-10 table into README
├── requirements.txt
└── README.md
```

---

## Licenses and Data Sources

This project is based on open data and requires the following attribution for any further use:

### 1. Atmospheric Data (Ozone)
The ozone forecast values are provided by the **Copernicus Atmosphere Monitoring Service (CAMS)**.
- **Data Source:** [CAMS European Air Quality Forecasts](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts)
- **License:** [Copernicus Data License (CC-BY 4.0)](https://doc.ecmwf.int/display/CAS/Copernicus+Data+License)
- **Attribution:** *Generated using Copernicus Atmosphere Monitoring Service information 2026.*

### 2. Administrative Boundaries (Municipalities)
The geographical centroids and names of the municipalities are based on data from the Federal Agency for Cartography and Geodesy (BKG).
- **Data Source:** © GeoBasis-DE / BKG 2013 (data modified).

---

## Notes

- The CAMS forecast is updated once per day (00:00 UTC model run).
- All timestamps in the output are in **UTC**.
- `peak_ozone_ug_m3` is `null` when no forecast data is available for that day (e.g. beyond the 96-hour window).
- The 11 × 11 km grid resolution means that municipalities within the same grid cell will share the same value.
