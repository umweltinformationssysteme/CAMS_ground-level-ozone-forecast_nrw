# NRW Ozone Forecast

Daily 3-day ground-level ozone forecast for all municipalities in North Rhine-Westphalia (NRW), Germany.  
Data source: [CAMS European Air Quality Forecasts](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts) — ensemble model, surface level (0 m).

---

<!-- TOP10_START -->
*Table will appear here after the first workflow run.*
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

## Notes

- The CAMS forecast is updated once per day (00:00 UTC model run).
- All timestamps in the output are in **UTC**.
- `peak_ozone_ug_m3` is `null` when no forecast data is available for that day (e.g. beyond the 96-hour window).
- The 11 × 11 km grid resolution means that municipalities within the same grid cell will share the same value.
