import pandas as pd
import numpy as np

from multiprocessing import Pool
from functools import partial
from typing import List

import tqdm
import pytz
import ta

ny_tz = pytz.timezone('America/New_York')

def create_z(
    df: pd.Series,
    lag_minute: int,
    feature: str = 'close'
):
    df_result = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc=f'z_{lag_minute}'):
        if df_day.shape[0] == 0:
            continue
        df_day = df_day.copy()

        mean = df_day[feature].rolling(lag_minute).mean()
        std = df_day[feature].rolling(lag_minute).std()

        df_day[f'z_{feature}_{lag_minute}m'] = (df_day[feature] - mean) / std
        df_day[f'pct_{feature}_{lag_minute}m'] = (df_day[feature] - mean) / mean
        df_day[f'std_{feature}_{lag_minute}m'] = std
        df_day[f'sma_{feature}_{lag_minute}m'] = mean

        df_result.append(df_day)

    df_result = pd.concat(df_result)

    return df_result

def create_lag(
    df: pd.DataFrame,
    feature: str,
    lag_minute: int
):
    timestamp = df['datetime'].copy()
    fast_forward_time = timestamp + pd.Timedelta(minutes=lag_minute)
    fast_forward_time = fast_forward_time.dt.tz_convert(ny_tz)

    feature_name = 'lag'
    feature_name = f'{feature_name}{lag_minute}m'
    feature_name = f'{feature_name}_{feature}'

    df_lag = pd.DataFrame({'datetime': fast_forward_time, feature_name: df[feature].copy()})
    df = pd.merge(df, df_lag, on='datetime', how='left')
    # df[feature_name] = df[feature_name].fillna(0)

    return df

def create_rsi(
    df: pd.DataFrame,
    periods: List[int]
):
    df_result = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc='rsi'):
        if df_day.shape[0] == 0:
            continue
        df_day = df_day.copy()
        for period in periods:
            df_day[f'rsi_{period}'] = ta.momentum.rsi(close=df_day['close'], window=period).copy()
            df_day[f'rsi_{period}_signal'] = pd.cut(df_day[f'rsi_{period}'], bins=[0, 30, 70, 100])

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
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc='dst'):
        if df_day.shape[0] == 0:
            continue
        
        df_day = df_day.copy()
        for period_minute in period_minutes:
            high = df_day[feature].rolling(period_minute).max()
            low = df_day[feature].rolling(period_minute).min()
            mean = df_day[feature].rolling(period_minute).mean()
            df_day[f'dst_high_{period_minute}m'] = (df_day[feature] - high) / high
            df_day[f'dst_low_{period_minute}m'] = (df_day[feature] - low) / low
            df_day[f'dst_mean_{period_minute}m'] = (df_day[feature] - mean) / mean
            df_day[f'dst_mean_high_{period_minute}m'] = (mean - high) / high
            df_day[f'dst_mean_low_{period_minute}m'] = (mean - low) / low

        df_result.append(df_day)

    df_result = pd.concat(df_result)

    return df_result

def create_ma_ratio(
    df: pd.DataFrame,
    short: int,
    long: int,
    feature: str = 'close'
):
    df_result = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc=f'ma_ratio_{short}_{long}'):
        if df_day.shape[0] == 0:
            continue
        
        df_day = df_day.copy()
        ma_short = df_day[feature].rolling(short).mean()
        ma_long = df_day[feature].rolling(long).mean()
        df_day[f'ma_ratio_{short}_{long}'] = (ma_short / ma_long)

        df_result.append(df_day)
    
    df_result = pd.concat(df_result)

    return df_result

def create_bollinger_band(
    df: pd.DataFrame,
    period: int
):
    df_result = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc=f'bollinger_band_{period}'):
        if df_day.shape[0] == 0:
            continue
        
        df_day = df_day.copy()
        indicator_bb = ta.volatility.BollingerBands(close=df_day['close'], window=period)
        high = indicator_bb.bollinger_hband()
        low = indicator_bb.bollinger_lband()

        df_day['bb_high'] = high.sub(df_day.close).div(high).apply(np.log1p)
        df_day['bb_low'] = low.sub(df_day.close).div(low).apply(np.log1p)

        df_result.append(df_day)
    
    df_result = pd.concat(df_result)

    return df_result
