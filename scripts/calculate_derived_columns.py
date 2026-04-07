import os
import pandas as pd
import mysql.connector

from transform_qcom_1m import add_transformed_columns

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_NAME = os.getenv("DB_NAME", "finance")
DB_USER = os.getenv("DB_USER", "stockuser")
DB_PASS = os.getenv("DB_PASS", "stockPass")
TICKER = os.getenv("TICKER", "QCOM")


def safe_float(value):
    if value is None or pd.isna(value):
        return None
    return float(value)


def safe_int(value):
    if value is None or pd.isna(value):
        return None
    return int(value)


def load_existing_data():
    conn = mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

    query = """
    SELECT
        ticker,
        datetime_utc,
        open_price,
        high_price,
        low_price,
        close_price,
        volume
    FROM stock_prices_1m
    WHERE ticker = %s
    ORDER BY datetime_utc ASC
    """

    df = pd.read_sql(query, conn, params=(TICKER,))
    conn.close()

    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"])
    return df


def write_backfill(df):
    conn = mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    cur = conn.cursor()

    sql = """
    UPDATE stock_prices_1m
    SET
        price_gain = %s,
        return_pct = %s,
        log_return = %s,
        realized_vol_20 = %s,
        realized_vol_60 = %s,
        cumulative_gain = %s,
        volume_zscore = %s,
        unusual_move_flag = %s,
        unusual_volume_flag = %s,
        unusual_vol_flag = %s
    WHERE ticker = %s AND datetime_utc = %s
    """

    rows_written = 0

    for _, row in df.iterrows():
        values = (
            safe_float(row["price_gain"]),
            safe_float(row["return_pct"]),
            safe_float(row["log_return"]),
            safe_float(row["realized_vol_20"]),
            safe_float(row["realized_vol_60"]),
            safe_float(row["cumulative_gain"]),
            safe_float(row["volume_zscore"]),
            safe_int(row["unusual_move_flag"]),
            safe_int(row["unusual_volume_flag"]),
            safe_int(row["unusual_vol_flag"]),
            row["ticker"],
            row["datetime_utc"].to_pydatetime()
        )
        cur.execute(sql, values)
        rows_written += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Backfilled rows: {rows_written}")


def main():
    df = load_existing_data()

    if df.empty:
        print("No rows found.")
        return

    df = add_transformed_columns(df)
    write_backfill(df)
    print("Backfill complete.")


if __name__ == "__main__":
    main()
