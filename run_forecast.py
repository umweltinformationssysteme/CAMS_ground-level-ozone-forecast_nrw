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
OUTPUT_JSON        = "output/ozone_forecast_nrw.json"
OUTPUT_NC          = "ozone_forecast.nc"
NRW_BBOX           = [52.6, 5.8, 50.3, 9.5]   # [N, W, S, E]
ALL_LEAD_HOURS     = [str(h) for h in range(0, 97)]


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
    Lead hours 0-96 cover today + 2 more days at hourly resolution.
    """
    api_key = os.environ.get("CDS_API_KEY")
    api_url = os.environ.get("CDS_API_URL", "https://ads.atmosphere.copernicus.eu/api")

    client = cdsapi.Client(url=api_url, key=api_key)
    client.retrieve(
        "cams-europe-air-quality-forecasts",
        {
            "variable":      "ozone",
            "model":         "ensemble",
            "level":         "0",
            "date":          f"{today}/{today}",
            "type":          "forecast",
            "time":          "00:00",
            "leadtime_hour": ALL_LEAD_HOURS,
            "area":          NRW_BBOX,
            "format":        "netcdf",
        },
        output_path,
    )


# ---------------------------------------------------------------------------
# 3. Build an absolute DatetimeIndex from the raw NetCDF time axis
# ---------------------------------------------------------------------------
def build_time_index(ds: xr.Dataset, forecast_base: str) -> pd.DatetimeIndex:
    """
    CAMS NetCDF files store the time axis as lead-time offsets (timedeltas),
    NOT as absolute timestamps.  The values are integers 0, 1, 2, ..., 96
    representing hours since the forecast base time (00:00 UTC on forecast_base).

    xarray >= 2024 no longer auto-decodes these into timedelta64 and emits
    a FutureWarning; when decoded they become nanosecond-epoch values if
    mishandled.  We therefore read the raw integers and add the known forecast
    origin ourselves, which is always today at 00:00 UTC.
    """
    origin = pd.Timestamp(forecast_base, tz="UTC")

    time_var = ds["time"]
    raw      = time_var.values          # e.g. array([0, 1, 2, ..., 96])
    units    = time_var.attrs.get("units", "")

    print(f"  time raw[:5] : {raw[:5]}")
    print(f"  time units   : '{units}'")

    # --- Strategy A: CF 'units' attribute present (e.g. "hours since ...") ---
    if "since" in units:
        unit_part, origin_part = units.split("since", 1)
        unit_str   = unit_part.strip().lower().rstrip("s")  # "hour","second",...
        # Strip trailing timezone tokens like " 0:00" or " 00:00"
        origin_str = origin_part.strip()
        for suffix in [" 0:00", " 00:00", "+00:00", "Z"]:
            origin_str = origin_str.removesuffix(suffix).strip()

        unit_map = {"hour": "h", "second": "s", "minute": "min", "day": "D"}
        pd_unit  = unit_map.get(unit_str)

        if pd_unit:
            cf_origin = pd.Timestamp(origin_str, tz="UTC")
            deltas    = pd.to_timedelta(raw.astype(float), unit=pd_unit)
            times     = pd.DatetimeIndex([cf_origin + d for d in deltas])
            print(f"  decoded via CF units | first={times[0]} | last={times[-1]}")
            return times

    # --- Strategy B: no usable units — treat raw values as lead hours and
    #     anchor to the known forecast base date (today 00:00 UTC) ----------
    print("  WARNING: no CF units found; treating raw values as integer lead hours")
    deltas = pd.to_timedelta(raw.astype(float), unit="h")
    times  = pd.DatetimeIndex([origin + d for d in deltas])
    print(f"  decoded via lead-hour fallback | first={times[0]} | last={times[-1]}")
    return times


# ---------------------------------------------------------------------------
# 4. Extract per-municipality daily peak values
# ---------------------------------------------------------------------------
def extract_daily_peaks(
    nc_path: str, municipalities: pd.DataFrame, today: str
) -> dict:
    """
    For each municipality return the daily peak o3_conc (µg/m³) and the
    UTC timestamp of that peak for D+0, D+1 and D+2.
    """
    # decode_times=False  → keep raw numeric time values so we control decoding
    # decode_timedelta=False → suppress FutureWarning
    ds = xr.open_dataset(nc_path, decode_times=False, decode_timedelta=False)

    print(f"NetCDF variables  : {list(ds.data_vars)}")
    print(f"NetCDF dimensions : {dict(ds.sizes)}")

    # Nearest-neighbour lookup for all municipality centroids at once
    lats = xr.DataArray(municipalities["lat"].values, dims="municipality")
    lons = xr.DataArray(municipalities["lon"].values, dims="municipality")

    ozone_da = ds["o3_conc"].sel(latitude=lats, longitude=lons, method="nearest")

    # Squeeze out the singleton level dimension if present
    if "level" in ozone_da.dims:
        ozone_da = ozone_da.isel(level=0)

    # ozone_all shape: (time, municipality)
    ozone_all = ozone_da.values
    print(f"ozone_all shape   : {ozone_all.shape}")

    # Decode the absolute UTC timestamps for the time axis
    times = build_time_index(ds, today)
    ds.close()

    today_dt   = pd.Timestamp(today, tz="UTC")
    day_labels = ["today", "tomorrow", "day_after_tomorrow"]
    results    = {}

    for i, row in municipalities.iterrows():
        name  = row["name"]
        entry = {}

        for offset, label in enumerate(day_labels):
            target_date = (today_dt + pd.Timedelta(days=offset)).date()

            # Select all time steps that fall on the target calendar day (UTC)
            mask = np.array([t.date() == target_date for t in times])

            if not mask.any():
                entry[label] = {"peak_ozone_ug_m3": None, "peak_time_utc": None}
                continue

            daily_vals  = ozone_all[mask, i]
            daily_times = times[mask]

            peak_idx  = int(np.argmax(daily_vals))
            peak_val  = float(daily_vals[peak_idx])
            peak_time = daily_times[peak_idx]

            entry[label] = {
                "peak_ozone_ug_m3": round(peak_val, 2),
                "peak_time_utc":    peak_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

        results[name] = entry

    return results


# ---------------------------------------------------------------------------
# 5. Build and save output JSON
# ---------------------------------------------------------------------------
def save_output(
    results: dict, municipalities: pd.DataFrame, output_path: str, today: str
) -> None:
    """Merge forecast results with municipality metadata and write JSON."""
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
        output["municipalities"].append({
            "name":     name,
            "lat":      row["lat"],
            "lon":      row["lon"],
            "forecast": results.get(name, {}),
        })

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
