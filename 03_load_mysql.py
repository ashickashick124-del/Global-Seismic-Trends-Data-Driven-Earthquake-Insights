"""
Step 3: Store the cleaned dataset in MySQL.
Edit the DB_CONFIG values below (or set them as environment variables) before running.
"""

import os
import pandas as pd
from sqlalchemy import create_engine

INPUT_FILE = "earthquake_final.csv"
TABLE_NAME = "earthquakes"

DB_CONFIG = {
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "my-password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "3306"),
    "database": os.getenv("DB_NAME", "earthquake_db"),
}


def get_engine():
    url = (
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    return create_engine(url)


def main():
    df = pd.read_csv(INPUT_FILE, parse_dates=["time", "updated"])
    engine = get_engine()

    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False, chunksize=1000)
    print(f"Loaded {len(df)} rows into '{DB_CONFIG['database']}.{TABLE_NAME}'")


if __name__ == "__main__":
    main()
