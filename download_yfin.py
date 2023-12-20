from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
import time

# 15m data can only retrieve up to 60 days
# 1m data can only retrieve up to 30 days
cl = []
bf = []
for i in range(0, 28, 7):
    yfin_cl = yf.download('CL=F', interval='1m', start=datetime.today() - timedelta(days=i+7), end=datetime.today() - timedelta(days=i))
    yfin_bf = yf.download('BZ=F', interval='1m', start=datetime.today() - timedelta(days=i+7), end=datetime.today() - timedelta(days=i))
    cl.append(yfin_cl)
    bf.append(yfin_bf)
    time.sleep(3)

cl = pd.concat(cl)
bf = pd.concat(bf)

cl = cl.sort_values('Datetime')
bf = bf.sort_values('Datetime')

today = datetime.now().strftime('%Y%m%d_%H%M')
cl.to_csv(f'data/yahoo_finance/yfin_{today}_cl.csv')
bf.to_csv(f'data/yahoo_finance/yfin_{today}_bf.csv')