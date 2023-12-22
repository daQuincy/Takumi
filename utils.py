import pandas as pd

import pytz

def read_bm_data(file_path):
    df_wti = pd.read_csv(
        file_path,
        sep=';', header=0,
        names=['date', 'time', 'open', 'high', 'low', 'close', 'volume'],
        engine='c'
    )

    df_wti['date'] = pd.to_datetime(df_wti['date'], format='%d/%m/%Y')
    df_wti['date'] = df_wti['date'].dt.strftime('%m-%d-%Y')

    df_wti['datetime'] = pd.to_datetime(df_wti['date'] + ' ' + df_wti['time'])

    df_wti['datetime'] = df_wti['datetime'].dt.tz_localize('Etc/GMT+6')
    ny_tz = pytz.timezone('America/New_York')
    df_wti['datetime'] = df_wti['datetime'].dt.tz_convert(ny_tz)
    df_wti['datetime'] = pd.to_datetime(df_wti['datetime'])
    df_wti['date'] = df_wti['datetime'].dt.strftime('%Y-%m-%d')
    df_wti['time'] = df_wti['datetime'].dt.strftime('%H%M')
    df_wti['day'] = df_wti['datetime'].dt.strftime('%A')

    return df_wti