import os
import time
import requests
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta, timezone

TICKER = os.getenv("TICKER", "QCOM")
DAYS_BACK = int(os.getenv("DAYS_BACK", "8"))
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "1.0"))

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_NAME = os.getenv("DB_NAME", "finance")
DB_USER = os.getenv("DB_USER", "stockuser")
DB_PASS = os.getenv("DB_PASS", "stockPass")


def yahoo_1m_chunk(ticker: str, start_dt_utc: datetime, end_dt_utc: datetime, session=None) -> pd.DataFrame:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {
        "period1": int(start_dt_utc.timestamp()),
        "period2": int(end_dt_utc.timestamp()),
        "interval": "1m",
        "includePrePost": "false",
        "events": "div,splits"
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    s = session or requests.Session()
    r = s.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()

    chart = data.get("chart", {})
    if chart.get("error"):
        raise RuntimeError(chart["error"])

    result = chart.get("result")
    if not result:
        return pd.DataFrame()

    result = result[0]
    ts = result.get("timestamp", [])
    if not ts:
        return pd.DataFrame()

    q = result["indicators"]["quote"][0]
    df = pd.DataFrame({
        "datetime_utc": pd.to_datetime(ts, unit="s", utc=True),
        "open_price": q.get("open", []),
        "high_price": q.get("high", []),
        "low_price": q.get("low", []),
        "close_price": q.get("close", []),
        "volume": q.get("volume", []),
    }).dropna(subset=["close_price"])

    return df.reset_index(drop=True)


def save_to_database(df: pd.DataFrame, ticker: str):
    if df.empty:
        print("No data returned, nothing to save.")
        return

    conn = mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

    cur = conn.cursor()

    sql = """
    INSERT INTO stock_prices_1m
    (ticker, datetime_utc, open_price, high_price, low_price, close_price, volume)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
      open_price = VALUES(open_price),
      high_price = VALUES(high_price),
      low_price = VALUES(low_price),
      close_price = VALUES(close_price),
      volume = VALUES(volume)
    """

    rows_inserted = 0

    for _, row in df.iterrows():
        dt_value = row["datetime_utc"].to_pydatetime().replace(tzinfo=None)
        values = (
            ticker,
            dt_value,
            None if pd.isna(row["open_price"]) else float(row["open_price"]),
            None if pd.isna(row["high_price"]) else float(row["high_price"]),
            None if pd.isna(row["low_price"]) else float(row["low_price"]),
            None if pd.isna(row["close_price"]) else float(row["close_price"]),
            None if pd.isna(row["volume"]) else int(row["volume"]),
        )
        cur.execute(sql, values)
        rows_inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Inserted/updated rows: {rows_inserted}")


def main():
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=DAYS_BACK)

    s = requests.Session()
    print(f"Fetching {TICKER} 1m data: {start.isoformat()} -> {now.isoformat()}")

    new_df = yahoo_1m_chunk(TICKER, start, now, session=s)
    time.sleep(SLEEP_SEC)

    if new_df.empty:
        print("No rows fetched from Yahoo Finance.")
        return

    new_df = new_df.dropna(subset=["datetime_utc"])
    new_df = new_df.sort_values("datetime_utc").drop_duplicates(subset=["datetime_utc"], keep="last").reset_index(drop=True)

    save_to_database(new_df, TICKER)

    print("Done.")


if __name__ == "__main__":
    main()
