import pandas as pd
import numpy as np

from multiprocessing import Pool
from functools import partial
from typing import List

import tqdm
import pytz
import ta

ny_tz = pytz.timezone('America/New_York')

def z_past(
    sr: pd.Series,
    df_1m: pd.DataFrame,
    lag_hr: int,
    lag_minute: int,
    name: str,
    trend_threshold: float = 0.5,
    feature: str = 'close'
):
    timestamp = sr['datetime']
    start = timestamp - pd.Timedelta(hours=lag_hr, minutes=lag_minute)
    df_past = df_1m[
        (df_1m['datetime'] >= start) & 
        (df_1m['datetime'] < timestamp)
    ]

    if df_past.shape[0] == 0:
        mean = sr[feature]
        std = 0
        z = 0
        pct = 0
    else:
        mean = df_past[feature].mean()
        std = df_past[feature].std()

        # prevent division by 0
        if std == 0:
            std = np.nan

        z = (sr[feature] - mean) / std
        pct = np.round(((sr[feature] - mean) / mean) * 100, 2)

    sr[f'z_{name}'] = z
    sr[f'pct_{name}'] = pct
    sr[f'mean_{name}'] = mean
    sr[f'std_{name}'] = std

    if z > trend_threshold:
        sr[f'trend_{name}'] = 'up'
    elif z < -trend_threshold:
        sr[f'trend_{name}'] = 'down'
    else:
        sr[f'trend_{name}'] = 'neutral'

    return sr

def compute_z_past(
    df: pd.Series,
    df_1m: pd.DataFrame,
    lag_hr: int,
    lag_minute: int,
    name: str,
    trend_threshold: float = 0.5,
    feature: str = 'close'
):
    df_data_sr = df.to_dict(orient='records')
    partial_function = partial(
        z_past, df_1m=df_1m, lag_hr=lag_hr, lag_minute=lag_minute, name=name, trend_threshold=trend_threshold, feature=feature
    )
    with Pool(10) as p:
        df_data = list(p.starmap(partial_function, [(element,) for element in df_data_sr]))
    df_data = pd.DataFrame(df_data)

    return df_data


def create_lag(
    df: pd.DataFrame,
    feature: str,
    lag_hr: int,
    lag_minute: int
):
    timestamp = df['datetime']
    fast_forward_time = timestamp + pd.Timedelta(hours=lag_hr, minutes=lag_minute)
    fast_forward_time = fast_forward_time.dt.tz_convert(ny_tz)

    feature_name = 'lag'
    if lag_hr != 0: feature_name = f'{feature_name}{lag_hr}hr'
    if lag_minute != 0: feature_name = f'{feature_name}{lag_minute}m'
    feature_name = f'{feature_name}_{feature}'

    df_lag = pd.DataFrame({'datetime': fast_forward_time, feature_name: df['z_15m']})
    df = pd.merge(df, df_lag, on='datetime', how='left')
    df[feature_name] = df[feature_name].fillna(0)

    return df

def create_rsi(
    df: pd.DataFrame,
    periods: List[int]
):
    df_result = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D'))):
        if df_day.shape[0] == 0:
            continue
        
        for period in periods:
            df_day[f'rsi_{period}'] = ta.momentum.rsi(close=df_day['close'], window=period).copy()

        df_result.append(df_day)

    df_result = pd.concat(df_result)
    
    return df_result

def create_dst(
    df: pd.DataFrame,
    period_minutes: List[int],
    feature: str = 'close'
):
    """
    Distance of current close price to the high of the past <period minute>
    """

    df_result = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D'))):
        if df_day.shape[0] == 0:
            continue
        
        feature_value = df[feature].copy()
        for period_minute in period_minutes:
            high = df_day[feature].rolling(period_minute).max().copy()
            low = df_day[feature].rolling(period_minute).min().copy()
            mean = df_day[feature].rolling(period_minute).mean().copy()
            df_day[f'dst_high_{period_minute}m'] = (feature_value - high) / high
            df_day[f'dst_low_{period_minute}m'] = (feature_value - low) / low
            df_day[f'dst_mean_{period_minute}m'] = (feature_value - mean) / mean
            df_day[f'dst_mean_high_{period_minute}m'] = (mean - high) / high
            df_day[f'dst_mean_low_{period_minute}m'] = (mean - low) / low

        df_result.append(df_day)

    df_result = pd.concat(df_result)

    return df_result
