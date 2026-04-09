import os
import glob
import pandas as pd

from transform_qcom_1m import add_transformed_columns
from fetch_qcom_1m_weekly import save_to_database, TICKER

CSV_FOLDER = os.getenv("CSV_FOLDER", os.path.expanduser("~/project/programming/data"))
CSV_PATTERN = os.getenv("CSV_PATTERN", "QCOM*.csv")


def load_and_combine_csvs():
    file_paths = sorted(glob.glob(os.path.join(CSV_FOLDER, CSV_PATTERN)))

    if not file_paths:
        raise FileNotFoundError(f"No CSV files found in {CSV_FOLDER} matching {CSV_PATTERN}")

    frames = []

    for path in file_paths:
        print(f"Reading: {path}")
        df = pd.read_csv(path)

        df = df.rename(columns={
            "open": "open_price",
            "high": "high_price",
            "low": "low_price",
            "close": "close_price",
        })

        required = [
            "datetime_utc",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "volume",
        ]

        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns {missing} in file: {path}")

        df = df[required].copy()
        df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], errors="coerce", utc=True).dt.tz_convert(None)
        df = df.dropna(subset=["datetime_utc", "close_price"])

        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("datetime_utc")
    combined = combined.drop_duplicates(subset=["datetime_utc"], keep="last").reset_index(drop=True)

    print(f"Combined rows after deduplication: {len(combined)}")
    return combined


def main():
    df = load_and_combine_csvs()
    df = add_transformed_columns(df)
    save_to_database(df, TICKER)
    print("CSV import complete.")


if __name__ == "__main__":
    main()
