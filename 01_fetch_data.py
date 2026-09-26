"""
Step 1: Dataset retrieval from the USGS Earthquake API.
Loops month-by-month over the last 5 years and pulls all events into one CSV.
"""

import requests
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# ---- CONFIG ----
YEARS_BACK = 5
MIN_MAGNITUDE = 2.5   # keeps each monthly request under USGS's 20,000-record cap
OUTPUT_FILE = "earthquake_raw.csv"


def month_ranges(years_back):
    """Yield (start, end) date strings covering each month for the last N years."""
    end = datetime.utcnow().replace(day=1)
    start = end - relativedelta(years=years_back)
    current = start
    while current < end:
        nxt = current + relativedelta(months=1)
        yield current.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")
        current = nxt


def fetch_month(starttime, endtime, minmagnitude=MIN_MAGNITUDE):
    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "minmagnitude": minmagnitude,
        "orderby": "time",
    }
    resp = requests.get(BASE_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def parse_features(geojson_data):
    rows = []
    for feature in geojson_data.get("features", []):
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [None, None, None])
        rows.append({
            "id": feature.get("id"),
            "time": props.get("time"),
            "updated": props.get("updated"),
            "latitude": coords[1],
            "longitude": coords[0],
            "depth_km": coords[2],
            "mag": props.get("mag"),
            "magType": props.get("magType"),
            "place": props.get("place"),
            "status": props.get("status"),
            "tsunami": props.get("tsunami"),
            "sig": props.get("sig"),
            "net": props.get("net"),
            "nst": props.get("nst"),
            "dmin": props.get("dmin"),
            "rms": props.get("rms"),
            "gap": props.get("gap"),
            "magError": props.get("magError"),
            "depthError": props.get("depthError"),
            "magNst": props.get("magNst"),
            "locationSource": props.get("locationSource"),
            "magSource": props.get("magSource"),
            "types": props.get("types"),
            "ids": props.get("ids"),
            "sources": props.get("sources"),
            "type": props.get("type"),
            "alert": props.get("alert"),
        })
    return rows


def main():
    all_rows = []
    for start, end in month_ranges(YEARS_BACK):
        print(f"Fetching {start} -> {end} ...")
        try:
            data = fetch_month(start, end)
            rows = parse_features(data)
            print(f"   {len(rows)} events")
            all_rows.extend(rows)
        except requests.exceptions.RequestException as e:
            print(f"   Failed for {start}-{end}: {e}")
        time.sleep(0.5)  # be polite to the API

    df = pd.DataFrame(all_rows)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved {len(df)} total rows to {OUTPUT_FILE}")
    print(df.shape)
    print(df.head())


if __name__ == "__main__":
    main()
