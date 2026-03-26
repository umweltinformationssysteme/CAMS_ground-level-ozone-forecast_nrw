# NRW Ozone Forecast

Daily 3-day ground-level ozone forecast for all municipalities in North Rhine-Westphalia (NRW), Germany.  
Data source: [CAMS European Air Quality Forecasts](https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-europe-air-quality-forecasts) — ensemble model, surface level (0 m).

---

## What it does

A GitHub Actions workflow runs every morning at **06:00 UTC**. It:

1. Downloads the CAMS 00:00 UTC ensemble ozone forecast (lead hours 0–96 h) for the NRW bounding box.
2. Maps each municipality centroid to the nearest 11 × 11 km grid cell.
3. Finds the **daily peak ozone value** for today, tomorrow and the day after tomorrow.
4. Writes the results to `output/ozone_forecast_nrw.json` and pushes the file back to this repository.

---

## Output format

`output/ozone_forecast_nrw.json`

```json
{
  "generated_at_utc": "2024-06-01T06:12:34Z",
  "forecast_base_date": "2024-06-01",
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
          "peak_time_utc": "2024-06-01T13:00:00Z"
        },
        "tomorrow": {
          "peak_ozone_ug_m3": 98.7,
          "peak_time_utc": "2024-06-02T14:00:00Z"
        },
        "day_after_tomorrow": {
          "peak_ozone_ug_m3": 105.1,
          "peak_time_utc": "2024-06-03T12:00:00Z"
        }
      }
    }
  ]
}
```

---

## Setup

### 1. Copernicus ADS account & API key

1. Register at <https://ads.atmosphere.copernicus.eu/>.
2. Accept the dataset licence for *CAMS European Air Quality Forecasts*.
3. Copy your **UID** and **API key** from your ADS profile page.

### 2. GitHub repository secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Name | Value |
|---|---|
| `CDS_API_KEY` | `<your-uid>:<your-api-key>` |
| `CDS_API_URL` | `https://ads.atmosphere.copernicus.eu/api/v2` |

### 3. Repository structure

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
├── requirements.txt
└── README.md
```

### 4. Manual trigger

You can trigger a run at any time via **Actions → NRW Ozone Forecast → Run workflow**.

---

## Local development

```bash
pip install -r requirements.txt

# Create ~/.cdsapirc with your credentials:
# url: https://ads.atmosphere.copernicus.eu/api/v2
# key: <uid>:<api-key>

python run_forecast.py
```

---

## Notes

- The CAMS forecast is updated once per day (00:00 UTC model run).
- All timestamps in the output are in **UTC**.
- `peak_ozone_ug_m3` is `null` when no forecast data is available for that day (e.g. beyond the 96-hour window).
- The 11 × 11 km grid resolution means that municipalities within the same grid cell will share the same value.
