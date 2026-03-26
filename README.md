# NRW Ozone Forecast

Daily 3-day ground-level ozone forecast for all municipalities in North Rhine-Westphalia (NRW), Germany.  
Data source: [CAMS European Air Quality Forecasts](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts) — ensemble model, surface level (0 m).

---

<!-- TOP10_START -->

## Top 10 — Highest Ozone Values Today (2026-03-26)

*Forecast base: 2026-03-26 00:00 UTC · Generated: 2026-03-26T11:26:00Z*

<table>
  <thead>
    <tr>
      <th align="left">Municipality</th>
      <th align="left">Peak time (UTC)</th>
      <th align="right">O₃ (µg/m³)</th>
    </tr>
  </thead>
  <tbody>
    <tr bgcolor="#FAE88E">
      <td><b>Preußisch Oldendorf</b></td>
      <td>2026-03-26 13:00 UTC</td>
      <td align="right"><b>100.3</b></td>
    </tr>
    <tr bgcolor="#FAE88E">
      <td><b>Stemwede</b></td>
      <td>2026-03-26 13:00 UTC</td>
      <td align="right"><b>100.3</b></td>
    </tr>
    <tr bgcolor="#EBEEB3">
      <td><b>Rahden</b></td>
      <td>2026-03-26 13:00 UTC</td>
      <td align="right"><b>100.0</b></td>
    </tr>
    <tr bgcolor="#EBEEB3">
      <td><b>Westerkappeln</b></td>
      <td>2026-03-26 15:00 UTC</td>
      <td align="right"><b>99.8</b></td>
    </tr>
    <tr bgcolor="#EBEEB3">
      <td><b>Mettingen</b></td>
      <td>2026-03-26 15:00 UTC</td>
      <td align="right"><b>99.6</b></td>
    </tr>
    <tr bgcolor="#EBEEB3">
      <td><b>Recke</b></td>
      <td>2026-03-26 15:00 UTC</td>
      <td align="right"><b>99.6</b></td>
    </tr>
    <tr bgcolor="#EBEEB3">
      <td><b>Rödinghausen</b></td>
      <td>2026-03-26 13:00 UTC</td>
      <td align="right"><b>99.5</b></td>
    </tr>
    <tr bgcolor="#EBEEB3">
      <td><b>Hüllhorst</b></td>
      <td>2026-03-26 13:00 UTC</td>
      <td align="right"><b>99.4</b></td>
    </tr>
    <tr bgcolor="#EBEEB3">
      <td><b>Hopsten</b></td>
      <td>2026-03-26 15:00 UTC</td>
      <td align="right"><b>99.3</b></td>
    </tr>
    <tr bgcolor="#EBEEB3">
      <td><b>Hörstel</b></td>
      <td>2026-03-26 12:00 UTC</td>
      <td align="right"><b>99.3</b></td>
    </tr>
  </tbody>
</table>

### Colour scale

<table>
  <tr>
    <td bgcolor="#C6E9F3" align="center"><small>≤20</small></td>
    <td bgcolor="#B3DFEB" align="center"><small>≤40</small></td>
    <td bgcolor="#A0D5E3" align="center"><small>≤60</small></td>
    <td bgcolor="#BFDFCD" align="center"><small>≤80</small></td>
    <td bgcolor="#EBEEB3" align="center"><small>≤100</small></td>
    <td bgcolor="#FAE88E" align="center"><small>≤120</small></td>
    <td bgcolor="#F5D362" align="center"><small>≤140</small></td>
    <td bgcolor="#EDB43C" align="center"><small>≤160</small></td>
    <td bgcolor="#E18620" align="center"><small>≤180</small></td>
    <td bgcolor="#D05C0B" align="center"><small>≤200</small></td>
    <td bgcolor="#AA4110" align="center"><small>≤240</small></td>
    <td bgcolor="#852615" align="center"><small>≤500</small></td>
    <td bgcolor="#8526BA" align="center"><small>>500</small></td>
  </tr>
</table>

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
