import os
import sys
import math
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from transform_qcom_1m import add_transformed_columns


def test_add_transformed_columns_creates_expected_fields():
    rows = 80
    base_time = pd.Timestamp("2026-02-01 09:30:00")

    df = pd.DataFrame({
        "datetime_utc": [base_time + pd.Timedelta(minutes=i) for i in range(rows)],
        "open_price": [100 + i * 0.1 for i in range(rows)],
        "high_price": [100.5 + i * 0.1 for i in range(rows)],
        "low_price": [99.5 + i * 0.1 for i in range(rows)],
        "close_price": [100 + i * 0.12 for i in range(rows)],
        "volume": [1000 + (i * 20) for i in range(rows)],
    })

    result = add_transformed_columns(df)

    expected_columns = [
        "price_gain",
        "return_pct",
        "log_return",
        "cumulative_gain",
        "realized_vol_20",
        "realized_vol_60",
        "volume_zscore",
        "unusual_move_flag",
        "unusual_volume_flag",
        "unusual_vol_flag",
    ]

    for col in expected_columns:
        assert col in result.columns

    assert pd.isna(result.loc[0, "price_gain"])
    assert pd.isna(result.loc[0, "return_pct"])
    assert pd.isna(result.loc[0, "log_return"])

    assert result["realized_vol_20"].notna().sum() > 0
    assert result["realized_vol_60"].notna().sum() > 0

    assert result.loc[1, "price_gain"] is not None
    assert result.loc[10, "cumulative_gain"] is not None

    assert set(result["unusual_move_flag"].dropna().unique()).issubset({0, 1})
    assert set(result["unusual_volume_flag"].dropna().unique()).issubset({0, 1})
    assert set(result["unusual_vol_flag"].dropna().unique()).issubset({0, 1})


def test_add_transformed_columns_calculates_expected_values_correctly():
    base_time = pd.Timestamp("2026-02-01 09:30:00")

    df = pd.DataFrame({
        "datetime_utc": [
            base_time,
            base_time + pd.Timedelta(minutes=1),
            base_time + pd.Timedelta(minutes=2),
        ],
        "open_price": [100.0, 102.0, 101.0],
        "high_price": [101.0, 103.0, 102.0],
        "low_price": [99.0, 101.0, 100.0],
        "close_price": [100.0, 102.0, 101.0],
        "volume": [1000, 1100, 900],
    })

    result = add_transformed_columns(df)

    expected_price_gain_row_1 = 2.0
    expected_price_gain_row_2 = -1.0

    expected_return_pct_row_1 = ((102.0 - 100.0) / 100.0) * 100
    expected_return_pct_row_2 = ((101.0 - 102.0) / 102.0) * 100

    expected_log_return_row_1 = math.log(102.0 / 100.0)
    expected_log_return_row_2 = math.log(101.0 / 102.0)

    expected_cumulative_gain_row_0 = 0.0
    expected_cumulative_gain_row_1 = 2.0
    expected_cumulative_gain_row_2 = 1.0

    assert np.isclose(result.loc[1, "price_gain"], expected_price_gain_row_1)
    assert np.isclose(result.loc[2, "price_gain"], expected_price_gain_row_2)

    assert np.isclose(result.loc[1, "return_pct"], expected_return_pct_row_1)
    assert np.isclose(result.loc[2, "return_pct"], expected_return_pct_row_2)

    assert np.isclose(result.loc[1, "log_return"], expected_log_return_row_1)
    assert np.isclose(result.loc[2, "log_return"], expected_log_return_row_2)

    assert np.isclose(result.loc[0, "cumulative_gain"], expected_cumulative_gain_row_0)
    assert np.isclose(result.loc[1, "cumulative_gain"], expected_cumulative_gain_row_1)
    assert np.isclose(result.loc[2, "cumulative_gain"], expected_cumulative_gain_row_2)
