"""
Step 2: Data preparation.
Cleans timestamps, extracts country via Regex, cleans text/numeric fields,
and adds derived columns (year, month, day, depth/magnitude categories).
"""

import re
import pandas as pd

INPUT_FILE = "earthquake_raw.csv"
OUTPUT_FILE = "earthquake_final.csv"

STRING_COLS = ["magType", "status", "net", "sources", "types", "type",
               "locationSource", "magSource", "alert"]
NUMERIC_COLS = ["mag", "depth_km", "nst", "dmin", "rms", "gap",
                 "magError", "depthError", "magNst", "sig", "tsunami"]


def extract_country(place):
    """
    Pull a country / region name out of USGS 'place' strings, e.g.:
      '10km SW of Ridgecrest, CA'        -> 'CA'
      '25km N of Suva, Fiji'             -> 'Fiji'
      'South of the Fiji Islands'        -> 'South of the Fiji Islands'
    Regex: take whatever follows the last comma; if there's no comma,
    fall back to the text after 'of'.
    """
    if not isinstance(place, str) or place.strip() == "":
        return "Unknown"

    match = re.search(r",\s*([A-Za-z .]+)$", place)
    if match:
        return match.group(1).strip()

    match = re.search(r"\bof\s+([A-Za-z .]+)$", place)
    if match:
        return match.group(1).strip()

    return place.strip()


def depth_category(depth):
    if pd.isna(depth):
        return "Unknown"
    if depth < 70:
        return "Shallow"
    elif depth < 300:
        return "Intermediate"
    return "Deep"


def magnitude_category(mag):
    if pd.isna(mag):
        return "Unknown"
    if mag < 3:
        return "Minor"
    elif mag < 4:
        return "Light"
    elif mag < 5:
        return "Moderate"
    elif mag < 6:
        return "Strong"
    elif mag < 7:
        return "Major"
    return "Great"


def main():
    df = pd.read_csv(INPUT_FILE)

    # --- datetime fields ---
    df["time"] = pd.to_datetime(df["time"], unit="ms", errors="coerce")
    df["updated"] = pd.to_datetime(df["updated"], unit="ms", errors="coerce")

    # --- regex: extract country from place ---
    df["country"] = df["place"].apply(extract_country)

    # --- clean text fields ---
    for col in STRING_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": "Unknown", "": "Unknown"})

    # --- clean numeric fields ---
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())

    df["tsunami"] = df["tsunami"].fillna(0).astype(int)

    # --- drop rows with no usable location/magnitude ---
    df = df.dropna(subset=["latitude", "longitude", "mag"])

    # --- derived columns ---
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df["day"] = df["time"].dt.day
    df["day_of_week"] = df["time"].dt.day_name()
    df["hour"] = df["time"].dt.hour

    df["depth_category"] = df["depth_km"].apply(depth_category)
    df["magnitude_category"] = df["mag"].apply(magnitude_category)
    df["is_shallow"] = df["depth_km"] < 70
    df["is_destructive"] = df["mag"] >= 7.5

    df = df.drop_duplicates(subset=["id"])

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Cleaned dataset saved to {OUTPUT_FILE}")
    print(df.shape)
    print(df.dtypes)
    print(df.isna().sum())


if __name__ == "__main__":
    main()
