import pandas as pd
import numpy as np

ANNUALIZATION_FACTOR = np.sqrt(252 * 390)


def add_transformed_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.sort_values("datetime_utc").copy()

    df["price_gain"] = df["close_price"].diff()
    df["return_pct"] = df["close_price"].pct_change() * 100
    df["log_return"] = np.log(df["close_price"] / df["close_price"].shift(1))
    df["cumulative_gain"] = df["close_price"] - df["close_price"].iloc[0]

    df["realized_vol_20"] = df["log_return"].rolling(20).std() * ANNUALIZATION_FACTOR
    df["realized_vol_60"] = df["log_return"].rolling(60).std() * ANNUALIZATION_FACTOR

    vol_mean_20 = df["volume"].rolling(20).mean()
    vol_std_20 = df["volume"].rolling(20).std()
    df["volume_zscore"] = (df["volume"] - vol_mean_20) / vol_std_20

    abs_log_return = df["log_return"].abs()
    move_mean_60 = abs_log_return.rolling(60).mean()
    move_std_60 = abs_log_return.rolling(60).std()
    move_zscore = (abs_log_return - move_mean_60) / move_std_60
    df["unusual_move_flag"] = (move_zscore > 3).fillna(False).astype(int)

    df["unusual_volume_flag"] = (df["volume_zscore"] > 2).fillna(False).astype(int)

    vol_mean_60 = df["realized_vol_20"].rolling(60).mean()
    vol_std_60 = df["realized_vol_20"].rolling(60).std()
    vol_zscore = (df["realized_vol_20"] - vol_mean_60) / vol_std_60
    df["unusual_vol_flag"] = (vol_zscore > 2).fillna(False).astype(int)

    return df
