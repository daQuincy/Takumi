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
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc=f'z_{lag_minute} {feature}'):
        if df_day.shape[0] == 0:
            continue
        df_day = df_day.copy()

        mean = df_day[feature].rolling(lag_minute).mean()
        std = df_day[feature].rolling(lag_minute).std()

        df_day[f'z_{feature}_{lag_minute}m'] = (df_day[feature] - mean) / std
        df_day[f'pct_{feature}_{lag_minute}m'] = (df_day[feature] - mean) / mean
        df_day[f'std_{feature}_{lag_minute}m'] = std
        df_day[f'sma_{feature}_{lag_minute}m'] = mean

        # df_day = df_day.fillna(0)

        df_result.append(df_day)

    df_result = pd.concat(df_result)

    return df_result

def create_lag(
    df: pd.DataFrame,
    feature: str,
    lag_minute: int
):
    feature_name = 'lag'
    feature_name = f'{feature_name}{lag_minute}m'
    feature_name = f'{feature_name}_{feature}'

    df2 = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc=feature_name):
        if df_day.shape[0] == 0:
            continue
        df_day = df_day.copy()
        df_day[feature_name] = df_day[feature].shift(lag_minute).values
        df2.append(df_day)

    df2 = pd.concat(df2)

    return df2

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
            df_day[f'rsi_{period}'] = ta.momentum.rsi(close=df_day['close'], window=period).copy() / 100
            df_day[f'rsi_{period}_signal'] = pd.cut(df_day[f'rsi_{period}'], bins=[0, 30, 70, 100], labels=[0, 1, 2], ordered=False)

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
            df_day[f'dst_{feature}_high_{period_minute}m'] = (df_day[feature] - high) / high
            df_day[f'dst_{feature}_low_{period_minute}m'] = (df_day[feature] - low) / low
            df_day[f'dst_{feature}_mean_{period_minute}m'] = (df_day[feature] - mean) / mean
            df_day[f'dst_{feature}_mean_high_{period_minute}m'] = (mean - high) / high
            df_day[f'dst_{feature}_mean_low_{period_minute}m'] = (mean - low) / low

        # df_day = df_day.fillna(0)
        df_result.append(df_day)

    df_result = pd.concat(df_result)

    return df_result

def create_ma_ratio(
    df: pd.DataFrame,
    slow: int,
    fast: int,
    feature: str = 'close'
):
    df_result = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc=f'ma_ratio_{slow}_{fast}'):
        if df_day.shape[0] == 0:
            continue
        
        df_day = df_day.copy()
        ma_slow = df_day[feature].rolling(slow).mean()
        ma_fast = df_day[feature].rolling(fast).mean()
        df_day[f'ma_ratio_{slow}_{fast}'] = (ma_slow / ma_fast)

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

        df_day[f'bb_{period}_high'] = high.sub(df_day.close).div(high).apply(np.log1p)
        df_day[f'bb_{period}_low'] = low.sub(df_day.close).div(low).apply(np.log1p)

        df_result.append(df_day)
    
    df_result = pd.concat(df_result)

    return df_result


def create_money_flow_index(
    df: pd.DataFrame,
    window: int
):
    df_result = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc=f'mfi_{window}'):
        if df_day.shape[0] == 0:
            continue
        
        df_day = df_day.copy()
        df_day[f'mfi_{window}'] = ta.volume.money_flow_index(df_day.high, df_day.low, df_day.close, window) / 100

        df_result.append(df_day)

    df_result = pd.concat(df_result)

    return df_result

def create_macd_diff(
    df: pd.DataFrame,
    slow: int,
    fast: int,
    window: int 
):
    df_result = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc=f'macd_diff{window}_{slow}_{fast}'):
        if df_day.shape[0] == 0:
            continue
        
        df_day = df_day.copy()
        df_day[f'macd_diff{window}_{slow}_{fast}'] = ta.trend.macd_diff(df_day.close, slow, fast, window)

        df_result.append(df_day)

    df_result = pd.concat(df_result)

    return df_result

def create_ppo(
    df: pd.DataFrame,
    slow: int,
    fast: int,
    window: int 
):
    df_result = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc=f'ppo{window}_{slow}_{fast}'):
        if df_day.shape[0] == 0:
            continue
        
        df_day = df_day.copy()
        df_day[f'ppo{window}_{slow}_{fast}'] = ta.momentum.ppo(df_day.close)
        df_result.append(df_day)

    df_result = pd.concat(df_result)

    return df_result

def create_pvo(
    df: pd.DataFrame,
    slow: int,
    fast: int,
    window: int 
):
    df_result = []
    for day, df_day in tqdm.tqdm(df.groupby(pd.Grouper(key='datetime', freq='D')), desc=f'pvo{window}_{slow}_{fast}'):
        if df_day.shape[0] == 0:
            continue
        
        df_day = df_day.copy()
        df_day[f'pvo{window}_{slow}_{fast}'] = ta.momentum.pvo(df_day.volume)
        df_result.append(df_day)

    df_result = pd.concat(df_result)

    return df_result