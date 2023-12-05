from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd

# intraday data can only retrieve up to 60 days
yfin_cl = yf.download('CL=F', interval='15m', start=datetime.today() - timedelta(days=60), end=datetime.today())
yfin_bf = yf.download('BZ=F', interval='15m', start=datetime.today() - timedelta(days=60), end=datetime.today())

today = datetime.now().strftime('%Y%m%d_%H%M')
yfin_cl.to_csv(f'data/yfin_{today}_cl.csv')
yfin_bf.to_csv(f'data/yfin_{today}_bf.csv')