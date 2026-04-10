import pandas as pd
import mysql.connector

from fetch_qcom_1m_weekly import DB_HOST, DB_NAME, DB_USER, DB_PASS, TICKER


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )


def create_summary_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS monthly_summary_qcom (
            month_key VARCHAR(7) NOT NULL,
            ticker VARCHAR(20) NOT NULL,
            first_timestamp DATETIME NULL,
            last_timestamp DATETIME NULL,
            monthly_low DOUBLE NULL,
            monthly_high DOUBLE NULL,
            monthly_median_close DOUBLE NULL,
            first_close DOUBLE NULL,
            last_close DOUBLE NULL,
            monthly_gain_loss DOUBLE NULL,
            monthly_gain_loss_pct DOUBLE NULL,
            total_volume BIGINT NULL,
            avg_realized_vol_20 DOUBLE NULL,
            avg_realized_vol_60 DOUBLE NULL,
            row_count INT NULL,
            avg_log_return DOUBLE NULL,
            stddev_log_return DOUBLE NULL,
            avg_return_pct DOUBLE NULL,
            move_flag_count INT NULL,
            volume_flag_count INT NULL,
            vol_flag_count INT NULL,
            move_flag_ratio DOUBLE NULL,
            volume_flag_ratio DOUBLE NULL,
            vol_flag_ratio DOUBLE NULL,
            PRIMARY KEY (month_key, ticker)
        )
        '''
    )

    conn.commit()
    cur.close()
    conn.close()


def load_qcom_data() -> pd.DataFrame:
    conn = get_connection()

    query = '''
    SELECT
        datetime_utc,
        low_price,
        high_price,
        close_price,
        volume,
        realized_vol_20,
        realized_vol_60,
        log_return,
        return_pct,
        unusual_move_flag,
        unusual_volume_flag,
        unusual_vol_flag
    FROM stock_prices_1m
    WHERE ticker = %s
    ORDER BY datetime_utc ASC
    '''

    df = pd.read_sql(query, conn, params=(TICKER,))
    conn.close()

    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], errors="coerce")
    df = df.dropna(subset=["datetime_utc", "close_price"]).copy()
    return df


def build_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    df = df.sort_values("datetime_utc").copy()
    df["month_key"] = df["datetime_utc"].dt.to_period("M").astype(str)

    summary = (
        df.groupby("month_key")
        .agg(
            first_timestamp=("datetime_utc", "min"),
            last_timestamp=("datetime_utc", "max"),
            monthly_low=("low_price", "min"),
            monthly_high=("high_price", "max"),
            monthly_median_close=("close_price", "median"),
            first_close=("close_price", "first"),
            last_close=("close_price", "last"),
            total_volume=("volume", "sum"),
            avg_realized_vol_20=("realized_vol_20", "mean"),
            avg_realized_vol_60=("realized_vol_60", "mean"),
            row_count=("datetime_utc", "count"),
            avg_log_return=("log_return", "mean"),
            stddev_log_return=("log_return", "std"),
            avg_return_pct=("return_pct", "mean"),
            move_flag_count=("unusual_move_flag", "sum"),
            volume_flag_count=("unusual_volume_flag", "sum"),
            vol_flag_count=("unusual_vol_flag", "sum"),
        )
        .reset_index()
    )

    summary["ticker"] = TICKER
    summary["monthly_gain_loss"] = summary["last_close"] - summary["first_close"]
    summary["monthly_gain_loss_pct"] = (
        (summary["last_close"] - summary["first_close"]) / summary["first_close"]
    ) * 100

    summary["move_flag_ratio"] = summary["move_flag_count"] / summary["row_count"]
    summary["volume_flag_ratio"] = summary["volume_flag_count"] / summary["row_count"]
    summary["vol_flag_ratio"] = summary["vol_flag_count"] / summary["row_count"]

    return summary[
        [
            "month_key",
            "ticker",
            "first_timestamp",
            "last_timestamp",
            "monthly_low",
            "monthly_high",
            "monthly_median_close",
            "first_close",
            "last_close",
            "monthly_gain_loss",
            "monthly_gain_loss_pct",
            "total_volume",
            "avg_realized_vol_20",
            "avg_realized_vol_60",
            "row_count",
            "avg_log_return",
            "stddev_log_return",
            "avg_return_pct",
            "move_flag_count",
            "volume_flag_count",
            "vol_flag_count",
            "move_flag_ratio",
            "volume_flag_ratio",
            "vol_flag_ratio",
        ]
    ]


def as_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    return value


def save_monthly_summary(summary: pd.DataFrame):
    if summary.empty:
        print("No data found.")
        return

    conn = get_connection()
    cur = conn.cursor()

    sql = '''
    INSERT INTO monthly_summary_qcom
    (
        month_key, ticker, first_timestamp, last_timestamp,
        monthly_low, monthly_high, monthly_median_close,
        first_close, last_close, monthly_gain_loss, monthly_gain_loss_pct,
        total_volume, avg_realized_vol_20, avg_realized_vol_60, row_count,
        avg_log_return, stddev_log_return, avg_return_pct,
        move_flag_count, volume_flag_count, vol_flag_count,
        move_flag_ratio, volume_flag_ratio, vol_flag_ratio
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        first_timestamp = VALUES(first_timestamp),
        last_timestamp = VALUES(last_timestamp),
        monthly_low = VALUES(monthly_low),
        monthly_high = VALUES(monthly_high),
        monthly_median_close = VALUES(monthly_median_close),
        first_close = VALUES(first_close),
        last_close = VALUES(last_close),
        monthly_gain_loss = VALUES(monthly_gain_loss),
        monthly_gain_loss_pct = VALUES(monthly_gain_loss_pct),
        total_volume = VALUES(total_volume),
        avg_realized_vol_20 = VALUES(avg_realized_vol_20),
        avg_realized_vol_60 = VALUES(avg_realized_vol_60),
        row_count = VALUES(row_count),
        avg_log_return = VALUES(avg_log_return),
        stddev_log_return = VALUES(stddev_log_return),
        avg_return_pct = VALUES(avg_return_pct),
        move_flag_count = VALUES(move_flag_count),
        volume_flag_count = VALUES(volume_flag_count),
        vol_flag_count = VALUES(vol_flag_count),
        move_flag_ratio = VALUES(move_flag_ratio),
        volume_flag_ratio = VALUES(volume_flag_ratio),
        vol_flag_ratio = VALUES(vol_flag_ratio)
    '''

    rows_written = 0

    for _, row in summary.iterrows():
        values = (
            row["month_key"],
            row["ticker"],
            as_value(row["first_timestamp"]),
            as_value(row["last_timestamp"]),
            as_value(row["monthly_low"]),
            as_value(row["monthly_high"]),
            as_value(row["monthly_median_close"]),
            as_value(row["first_close"]),
            as_value(row["last_close"]),
            as_value(row["monthly_gain_loss"]),
            as_value(row["monthly_gain_loss_pct"]),
            as_value(row["total_volume"]),
            as_value(row["avg_realized_vol_20"]),
            as_value(row["avg_realized_vol_60"]),
            as_value(row["row_count"]),
            as_value(row["avg_log_return"]),
            as_value(row["stddev_log_return"]),
            as_value(row["avg_return_pct"]),
            as_value(row["move_flag_count"]),
            as_value(row["volume_flag_count"]),
            as_value(row["vol_flag_count"]),
            as_value(row["move_flag_ratio"]),
            as_value(row["volume_flag_ratio"]),
            as_value(row["vol_flag_ratio"]),
        )
        cur.execute(sql, values)
        rows_written += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Monthly rows inserted/updated: {rows_written}")


def main():
    create_summary_table()
    df = load_qcom_data()
    summary = build_monthly_summary(df)
    save_monthly_summary(summary)
    print("Monthly summary table updated.")


if __name__ == "__main__":
    main()
