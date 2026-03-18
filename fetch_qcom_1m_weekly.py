# scripts/fetch_qcom_1m_weekly.py
import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

TICKER = os.getenv("TICKER", "QCOM")
OUT_PATH = os.getenv("OUT_PATH", f"data/{TICKER}_1m.csv")
DAYS_BACK = int(os.getenv("DAYS_BACK", "8"))  # Yahoo 1m safe window
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "1.0"))

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
        "open": q.get("open", []),
        "high": q.get("high", []),
        "low": q.get("low", []),
        "close": q.get("close", []),
        "volume": q.get("volume", []),
    }).dropna(subset=["close"])

    return df.reset_index(drop=True)

def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=DAYS_BACK)

    s = requests.Session()
    print(f"Fetching {TICKER} 1m: {start.isoformat()} -> {now.isoformat()}")
    new_df = yahoo_1m_chunk(TICKER, start, now, session=s)
    time.sleep(SLEEP_SEC)

    if os.path.exists(OUT_PATH):
        old_df = pd.read_csv(OUT_PATH, parse_dates=["datetime_utc"])
        # Ensure timezone-aware
        old_df["datetime_utc"] = pd.to_datetime(old_df["datetime_utc"], utc=True, errors="coerce")
        df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        df = new_df

    df = df.dropna(subset=["datetime_utc"])
    df = df.sort_values("datetime_utc").drop_duplicates(subset=["datetime_utc"], keep="last").reset_index(drop=True)
    df.to_csv(OUT_PATH, index=False)

    print("Saved:", OUT_PATH)
    print("Rows:", len(df))

if __name__ == "__main__":
    main()
