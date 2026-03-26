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
    api_url = os.environ.get("CDS_API_URL", "https://ads.atmosphere.copernicus.eu/api")

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
# 3. Decode the time axis from a CAMS NetCDF file
# ---------------------------------------------------------------------------
def decode_time_axis(ds: xr.Dataset) -> pd.DatetimeIndex:
    """
    Robustly decode the 'time' variable from a CAMS NetCDF file.

    CAMS files use CF conventions: time is stored as numeric offsets
    (e.g. hours since a reference date) described by a 'units' attribute
    like 'hours since 2026-03-26 00:00:00'.

    xarray's decode_timedelta=False prevents auto-decoding into timedelta64,
    so we decode manually here using cftime/pandas to get a proper
    DatetimeIndex in UTC.
    """
    time_var = ds["time"]
    raw_values = time_var.values  # numeric offsets, e.g. float64 hours

    units = time_var.attrs.get("units", "")
    # units format: "hours since YYYY-MM-DD HH:MM:SS"
    # or "seconds since ..." etc.
    if "since" in units:
        parts = units.split("since", 1)
        unit_str = parts[0].strip().lower()   # e.g. "hours"
        origin_str = parts[1].strip()          # e.g. "2026-03-26 00:00:00"

        origin = pd.Timestamp(origin_str, tz="UTC")

        if unit_str in ("hour", "hours"):
            deltas = pd.to_timedelta(raw_values, unit="h")
        elif unit_str in ("second", "seconds"):
            deltas = pd.to_timedelta(raw_values, unit="s")
        elif unit_str in ("minute", "minutes"):
            deltas = pd.to_timedelta(raw_values, unit="m")
        elif unit_str in ("day", "days"):
            deltas = pd.to_timedelta(raw_values, unit="D")
        else:
            raise ValueError(f"Unsupported time unit: '{unit_str}' in '{units}'")

        return pd.DatetimeIndex([origin + d for d in deltas])

    # Fallback: try direct conversion (works if already datetime64)
    return pd.DatetimeIndex(pd.to_datetime(raw_values, utc=True))


# ---------------------------------------------------------------------------
# 4. Extract per-municipality daily peak values
# ---------------------------------------------------------------------------
def extract_daily_peaks(
    nc_path: str, municipalities: pd.DataFrame, today: str
) -> dict:
    """
    For each municipality, find the maximum ozone concentration (µg/m³)
    for D+0, D+1 and D+2 and the UTC hour at which that peak occurs.

    Returns a dict keyed by municipality name.
    """
    # decode_timedelta=False avoids a FutureWarning; we decode time manually
    ds = xr.open_dataset(nc_path, decode_timedelta=False)

    # Print available variables for debugging
    print(f"NetCDF variables: {list(ds.data_vars)}")
    print(f"NetCDF dimensions: {dict(ds.dims)}")

    # Build DataArrays for vectorised nearest-neighbour selection
    lats = xr.DataArray(municipalities["lat"].values, dims="municipality")
    lons = xr.DataArray(municipalities["lon"].values, dims="municipality")

    # shape: (time, municipality)
    ozone_all = (
        ds["o3_conc"]
        .sel(latitude=lats, longitude=lons, method="nearest")
        .values  # numpy array (time, municipality)
    )

    # Decode time axis robustly from CF units attribute
    times = decode_time_axis(ds)
    print(f"Time axis: {len(times)} steps, first={times[0]}, last={times[-1]}")

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
# 5. Build and save output JSON
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
