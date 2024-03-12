from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
import time

symbols = ['CL=F', 'BZ=F', 'GC=F']
for symbol in symbols:
    print(f'Downloading {symbol}')
    data = []
    for i in range(0, 28, 7):
        df_yfin = yf.download(symbol, interval='1m', start=datetime.today() - timedelta(days=i+7), end=datetime.today() - timedelta(days=i))
        time.sleep(0.5)
        data.append(df_yfin)

    df = pd.concat(data)
    df = df.sort_values('Datetime')

    # format to backtestmarket
    df['datetime'] = df.index
    df.columns = [x.lower() for x in df.columns]
    
    with pd.HDFStore('./large_files/yahoo.h5') as store:
        key = f'data/{symbol}'
        if key in store:
            df_old = store.get(key)
            df_new = pd.concat([df_old, df])
            df_new = df_new.drop_duplicates()
            print(f'[*] {df_new.shape[0] - df_old.shape[0]} rows added')
        else:
            df_new = df

        store.put(key, df, format='table')
