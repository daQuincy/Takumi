import pandas as pd
import numpy as np

from multiprocessing import Pool
from functools import partial

import tqdm

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
    