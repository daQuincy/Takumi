import pandas as pd
import datetime

assets = [('CL=F', 'cl'), ('BZ=F', 'cb'), ('GC=F', 'gc')]

source = 'data_20240312.h5'
destination = 'data_20240328.h5'

for asset in assets:
    with pd.HDFStore('./large_files/yahoo.h5') as store:
        df_yahoo = store.get(f'data/{asset[0]}')

    with pd.HDFStore(f'./large_files/{source}') as store:
        df = store.get(f'data/{asset[1]}')

    df_yahoo['day'] = df_yahoo.datetime.dt.day_name()
    df_yahoo['month'] = df_yahoo.datetime.dt.month
    df_yahoo['date'] = df_yahoo.datetime.dt.strftime('%Y-%m-%d')
    df_yahoo['time'] = df_yahoo.datetime.dt.strftime('%H%M')
    df_yahoo = df_yahoo.drop('adj close', axis=1)

    df_yahoo = df_yahoo[(df_yahoo['datetime'].dt.time >= datetime.time(hour=7, minute=0)) & (df_yahoo['datetime'].dt.hour <= 16)]
    df_result = []
    removed_day = []
    for day, df_day in df_yahoo.groupby(pd.Grouper(key='datetime', freq='D')):
        if df_day.shape[0] == 0:
            continue
        df_day = df_day.copy()
        df_day['datetime'] = pd.to_datetime(df_day['datetime'])

        df_trade_hour = df_day[(df_day['datetime'].dt.hour >= 9) & (df_day['datetime'].dt.hour < 16)]

        # allow up to 1 hour data missing in main trading hours
        if df_trade_hour.shape[0] < 360:
            print(f'{day} {df_trade_hour.shape[0]}')
            removed_day.append(day)
            continue

        year = day.year
        month = day.month
        day_of_month = day.day
        start_time = pd.Timestamp(year=year, month=month, day=day_of_month, hour=9, tz='America/New_York')
        end_time = pd.Timestamp(year=year, month=month, day=day_of_month, hour=15, minute=59, tz='America/New_York')
        desired_index = pd.to_datetime(pd.date_range(start=start_time, end=end_time, freq='T')).tolist()

        df_tmp = pd.DataFrame(desired_index, columns=['datetime'])
        df_trade_hour = pd.merge(df_trade_hour, df_tmp, how='outer', on='datetime').sort_values('datetime')

        df_trade_hour['date'] = df_trade_hour['datetime'].dt.strftime('%Y-%m-%d')
        df_trade_hour['time'] = df_trade_hour['datetime'].dt.strftime('%H%M')
        df_trade_hour['day'] = df_trade_hour['datetime'].dt.strftime('%A')
        df_trade_hour['month'] = df_trade_hour['datetime'].dt.month
        df_trade_hour[['open', 'high', 'low', 'close', 'volume']] = df_trade_hour[['open', 'high', 'low', 'close', 'volume']].interpolate(axis=0).round(2)
        df_trade_hour[['open', 'high', 'low', 'close', 'volume']] = df_trade_hour[['open', 'high', 'low', 'close', 'volume']].bfill(axis=0)
        df_trade_hour['volume'] = df_trade_hour['volume'].astype(int)
        
        df_day = pd.concat([df_day, df_trade_hour]).drop_duplicates(subset='datetime').sort_values('datetime')
        df_result.append(df_day)

    df_yahoo = pd.concat(df_result)
    df_merge = pd.concat([df, df_yahoo]).sort_values('datetime').reset_index(drop=True)
    df_merge = df_merge.drop_duplicates('datetime')

    with pd.HDFStore(f'./large_files/{destination}') as store:
        store.put(f'data/{asset[1]}', df_merge, format='table')