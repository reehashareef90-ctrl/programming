from flask import Flask, render_template
import mysql.connector
import os

from fetch_qcom_1m_weekly import DB_HOST, DB_NAME, DB_USER, DB_PASS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

app = Flask(
    __name__,
    template_folder=os.path.join(PROJECT_ROOT, "templates"),
    static_folder=os.path.join(PROJECT_ROOT, "static"),
)


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )


@app.route("/")
def dashboard():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        '''
        SELECT
            COUNT(*) AS total_rows,
            MIN(datetime_utc) AS start_date,
            MAX(datetime_utc) AS end_date
        FROM stock_prices_1m
        WHERE ticker = 'QCOM'
        '''
    )
    dataset_summary = cur.fetchone()

    cur.execute(
        '''
        SELECT COUNT(*) AS total_months
        FROM monthly_summary_qcom
        WHERE ticker = 'QCOM'
        '''
    )
    month_count = cur.fetchone()

    cur.execute(
        '''
        SELECT
            COALESCE(SUM(move_flag_count), 0) AS total_move_flags,
            COALESCE(SUM(volume_flag_count), 0) AS total_volume_flags,
            COALESCE(SUM(vol_flag_count), 0) AS total_vol_flags
        FROM monthly_summary_qcom
        WHERE ticker = 'QCOM'
        '''
    )
    flag_summary = cur.fetchone()

    cur.execute(
        '''
        SELECT *
        FROM monthly_summary_qcom
        WHERE ticker = 'QCOM'
        ORDER BY month_key
        '''
    )
    monthly_rows = cur.fetchall()

    cur.execute(
        '''
        SELECT
            datetime_utc,
            close_price,
            volume,
            return_pct,
            log_return,
            realized_vol_20,
            realized_vol_60,
            unusual_move_flag,
            unusual_volume_flag,
            unusual_vol_flag
        FROM stock_prices_1m
        WHERE ticker = 'QCOM'
        ORDER BY datetime_utc DESC
        LIMIT 20
        '''
    )
    recent_rows = cur.fetchall()

    if recent_rows:
        latest_close = recent_rows[0]["close_price"] or 0
        latest_vol20 = recent_rows[0]["realized_vol_20"] or 0
        latest_timestamp = recent_rows[0]["datetime_utc"]
    else:
        latest_close = 0
        latest_vol20 = 0
        latest_timestamp = None

    cur.execute(
        '''
        SELECT
            DATE(s.datetime_utc) AS chart_date,
            MAX(CASE WHEN s.datetime_utc = d.max_dt THEN s.close_price END) AS close_price,
            SUM(s.volume) AS volume,
            AVG(s.realized_vol_20) AS realized_vol_20,
            AVG(s.realized_vol_60) AS realized_vol_60,
            MAX(s.unusual_move_flag) AS unusual_move_flag,
            MAX(s.unusual_volume_flag) AS unusual_volume_flag,
            MAX(s.unusual_vol_flag) AS unusual_vol_flag
        FROM stock_prices_1m s
        JOIN (
            SELECT DATE(datetime_utc) AS day_key, MAX(datetime_utc) AS max_dt
            FROM stock_prices_1m
            WHERE ticker = 'QCOM'
            GROUP BY DATE(datetime_utc)
        ) d
          ON DATE(s.datetime_utc) = d.day_key
        WHERE s.ticker = 'QCOM'
        GROUP BY DATE(s.datetime_utc)
        ORDER BY DATE(s.datetime_utc) ASC
        '''
    )
    chart_rows = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        dataset_summary=dataset_summary,
        latest_close=latest_close,
        latest_vol20=latest_vol20,
        latest_timestamp=latest_timestamp,
        month_count=month_count,
        flag_summary=flag_summary,
        monthly_rows=monthly_rows,
        recent_rows=recent_rows,
        chart_rows=chart_rows,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
