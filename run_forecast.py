"""
NRW Ground-Level Ozone Forecast
Retrieves 3-day CAMS ensemble ozone forecasts for all NRW municipalities
and outputs the daily peak value + timestamp (UTC) per municipality as JSON.
"""

import os
import json
import cdsapi
import xarray as xr
import pandas as pd
import numpy as np
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MUNICIPALITIES_CSV = "municipality_nrw.csv"
OUTPUT_JSON = "output/ozone_forecast_nrw.json"
OUTPUT_NC = "ozone_forecast.nc"

# Bounding box: [N, W, S, E]
NRW_BBOX = [52.6, 5.8, 50.3, 9.5]

# Forecast lead hours to request (0–96 h, 1-hourly)
# We request all hours so we can find the daily peak
ALL_LEAD_HOURS = [str(h) for h in range(0, 97)]


# ---------------------------------------------------------------------------
# 1. Load municipality centroids
# ---------------------------------------------------------------------------
def load_municipalities(filepath: str) -> pd.DataFrame:
    """Load municipality names and centroid coordinates from CSV."""
    df = pd.read_csv(filepath)
    df = df.dropna(subset=["lat", "lon"])
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. Download CAMS forecast data
# ---------------------------------------------------------------------------
def download_cams_forecast(output_path: str, today: str) -> None:
    """
    Download CAMS European air quality ensemble forecast for ozone.
    Requests lead hours 0–96 starting from today's 00:00 UTC run,
    covering today, tomorrow and the day after tomorrow.
    """
    api_key = os.environ.get("CDS_API_KEY")
    api_url = os.environ.get("CDS_API_URL", "https://ads.atmosphere.copernicus.eu/api/v2")

    client = cdsapi.Client(url=api_url, key=api_key)

    client.retrieve(
        "cams-europe-air-quality-forecasts",
        {
            "variable": "ozone",
            "model": "ensemble",
            "level": "0",
            "date": f"{today}/{today}",
            "type": "forecast",
            "time": "00:00",
            "leadtime_hour": ALL_LEAD_HOURS,
            "area": NRW_BBOX,
            "format": "netcdf",
        },
        output_path,
    )


# ---------------------------------------------------------------------------
# 3. Extract per-municipality daily peak values
# ---------------------------------------------------------------------------
def extract_daily_peaks(
    nc_path: str, municipalities: pd.DataFrame, today: str
) -> dict:
    """
    For each municipality, find the maximum ozone concentration (µg/m³)
    for D+0, D+1 and D+2 and the UTC hour at which that peak occurs.

    Returns a dict keyed by municipality name.
    """
    ds = xr.open_dataset(nc_path)

    # Build DataArrays for vectorised nearest-neighbour selection
    lats = xr.DataArray(municipalities["lat"].values, dims="municipality")
    lons = xr.DataArray(municipalities["lon"].values, dims="municipality")

    # shape: (time, municipality)
    ozone_all = (
        ds["go3_conc"]
        .sel(latitude=lats, longitude=lons, method="nearest")
        .values  # numpy array (time, municipality)
    )

    # Timestamps from the NetCDF file
    times = pd.to_datetime(ds["time"].values)

    today_dt = pd.Timestamp(today, tz="UTC")
    day_offsets = [0, 1, 2]
    day_labels = ["today", "tomorrow", "day_after_tomorrow"]

    results = {}

    for i, row in municipalities.iterrows():
        name = row["name"]
        entry = {}

        for offset, label in zip(day_offsets, day_labels):
            target_date = (today_dt + pd.Timedelta(days=offset)).date()

            # Build a boolean mask for the target calendar day (UTC)
            mask = np.array([t.date() == target_date for t in times])

            if not mask.any():
                entry[label] = {"peak_ozone_ug_m3": None, "peak_time_utc": None}
                continue

            daily_vals = ozone_all[mask, i]
            daily_times = times[mask]

            peak_idx = int(np.argmax(daily_vals))
            peak_val = float(daily_vals[peak_idx])
            peak_time = daily_times[peak_idx]

            entry[label] = {
                "peak_ozone_ug_m3": round(peak_val, 2),
                "peak_time_utc": peak_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

        results[name] = entry

    ds.close()
    return results


# ---------------------------------------------------------------------------
# 4. Build and save output JSON
# ---------------------------------------------------------------------------
def save_output(results: dict, municipalities: pd.DataFrame, output_path: str, today: str) -> None:
    """
    Merge forecast results with municipality metadata and write to JSON.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    output = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "forecast_base_date": today,
        "data_source": "CAMS European Air Quality Forecasts (ensemble, level 0)",
        "unit": "µg/m³",
        "municipalities": [],
    }

    for _, row in municipalities.iterrows():
        name = row["name"]
        entry = {
            "name": name,
            "lat": row["lat"],
            "lon": row["lon"],
            "forecast": results.get(name, {}),
        }
        output["municipalities"].append(entry)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Output written to: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"Running NRW ozone forecast for base date: {today}")

    municipalities = load_municipalities(MUNICIPALITIES_CSV)
    print(f"Loaded {len(municipalities)} municipalities.")

    print("Downloading CAMS forecast data...")
    download_cams_forecast(OUTPUT_NC, today)
    print("Download complete.")

    print("Extracting daily peak values...")
    results = extract_daily_peaks(OUTPUT_NC, municipalities, today)

    save_output(results, municipalities, OUTPUT_JSON, today)
    print("Done.")


if __name__ == "__main__":
    main()
