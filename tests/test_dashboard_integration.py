import os
import sys
import math

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
sys.path.append(SCRIPTS_DIR)

import app as dashboard_app


def test_mysql_connection_and_basic_query():
    conn = dashboard_app.get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        '''
        SELECT COUNT(*) AS total_rows
        FROM stock_prices_1m
        WHERE ticker = 'QCOM'
        '''
    )
    row = cur.fetchone()

    cur.close()
    conn.close()

    assert row is not None
    assert row["total_rows"] > 0


def test_dashboard_route_returns_db_backed_page():
    dashboard_app.app.config["TESTING"] = True
    client = dashboard_app.app.test_client()

    response = client.get("/")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert "QCOM Market Data Dashboard" in html
    assert "Rows Collected" in html
    assert "Monthly Summary" in html


def test_known_timestamp_has_expected_stored_values():
    conn = dashboard_app.get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        '''
        SELECT
            datetime_utc,
            close_price,
            price_gain,
            return_pct,
            log_return,
            cumulative_gain
        FROM stock_prices_1m
        WHERE ticker = 'QCOM'
          AND datetime_utc = '2026-02-11 14:31:00'
        '''
    )
    row = cur.fetchone()

    cur.close()
    conn.close()

    assert row is not None

    assert math.isclose(float(row["close_price"]), 139.82000732421875, rel_tol=1e-9)
    assert math.isclose(float(row["price_gain"]), -0.214996337890625, rel_tol=1e-9)
    assert math.isclose(float(row["return_pct"]), -0.1535304261564452, rel_tol=1e-9)
    assert math.isclose(float(row["log_return"]), -0.0015364840488618415, rel_tol=1e-9)
    assert math.isclose(float(row["cumulative_gain"]), -0.214996337890625, rel_tol=1e-9)
