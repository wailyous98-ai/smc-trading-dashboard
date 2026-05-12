import ccxt
import pandas as pd
from datetime import datetime

exchange = ccxt.binance({'enableRateLimit': True})

def get_ohlcv(symbol='BTC/USDT', timeframe='1h', limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        print(f"خطأ: {e}")
        return None

def get_current_price(symbol='BTC/USDT'):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return {
            'price': ticker['last'],
            'high_24h': ticker['high'],
            'low_24h': ticker['low'],
            'change_24h': ticker['percentage'],
        }
    except Exception as e:
        print(f"خطأ: {e}")
        return None
