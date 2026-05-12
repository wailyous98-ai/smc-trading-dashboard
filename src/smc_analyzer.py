import sys
sys.path.insert(0, '/home/wail/trading_dashboard')
import pandas as pd
import numpy as np
from src.data_fetcher import get_ohlcv

def detect_swing_points(df, window=5):
    df['swing_high'] = df['high'][(df['high'] == df['high'].rolling(window, center=True).max())]
    df['swing_low'] = df['low'][(df['low'] == df['low'].rolling(window, center=True).min())]
    return df

def detect_bos_choch(df):
    """كشف BOS و CHoCH"""
    df['bos_bullish'] = False
    df['bos_bearish'] = False
    df['choch_bullish'] = False
    df['choch_bearish'] = False
    highs = df['swing_high'].dropna()
    lows = df['swing_low'].dropna()
    for i in range(2, len(df)):
        if len(highs) > 0:
            last_high = highs.iloc[-1]
            if df['close'].iloc[i] > last_high:
                df.loc[df.index[i], 'bos_bullish'] = True
        if len(lows) > 0:
            last_low = lows.iloc[-1]
            if df['close'].iloc[i] < last_low:
                df.loc[df.index[i], 'bos_bearish'] = True
        if i > 4:
            prev_highs = highs[highs.index < df.index[i]]
            prev_lows = lows[lows.index < df.index[i]]
            if len(prev_highs) >= 2:
                if df['close'].iloc[i] > prev_highs.iloc[-2]:
                    df.loc[df.index[i], 'choch_bullish'] = True
            if len(prev_lows) >= 2:
                if df['close'].iloc[i] < prev_lows.iloc[-2]:
                    df.loc[df.index[i], 'choch_bearish'] = True
    return df

def detect_order_blocks(df, window=3):
    """كشف Order Blocks"""
    df['ob_bullish'] = False
    df['ob_bearish'] = False
    df['ob_high'] = np.nan
    df['ob_low'] = np.nan
    for i in range(window, len(df)-1):
        if df['close'].iloc[i+1] > df['high'].iloc[i]:
            if df['close'].iloc[i] < df['open'].iloc[i]:
                df.loc[df.index[i], 'ob_bullish'] = True
                df.loc[df.index[i], 'ob_high'] = df['high'].iloc[i]
                df.loc[df.index[i], 'ob_low'] = df['low'].iloc[i]
        if df['close'].iloc[i+1] < df['low'].iloc[i]:
            if df['close'].iloc[i] > df['open'].iloc[i]:
                df.loc[df.index[i], 'ob_bearish'] = True
                df.loc[df.index[i], 'ob_high'] = df['high'].iloc[i]
                df.loc[df.index[i], 'ob_low'] = df['low'].iloc[i]
    return df

def detect_fvg(df):
    """كشف Fair Value Gaps"""
    df['fvg_bullish'] = False
    df['fvg_bearish'] = False
    df['fvg_top'] = np.nan
    df['fvg_bottom'] = np.nan
    for i in range(2, len(df)):
        if df['low'].iloc[i] > df['high'].iloc[i-2]:
            df.loc[df.index[i], 'fvg_bullish'] = True
            df.loc[df.index[i], 'fvg_top'] = df['low'].iloc[i]
            df.loc[df.index[i], 'fvg_bottom'] = df['high'].iloc[i-2]
        if df['high'].iloc[i] < df['low'].iloc[i-2]:
            df.loc[df.index[i], 'fvg_bearish'] = True
            df.loc[df.index[i], 'fvg_top'] = df['low'].iloc[i-2]
            df.loc[df.index[i], 'fvg_bottom'] = df['high'].iloc[i]
    return df

def detect_liquidity(df, window=10):
    df['liquidity_high'] = df['high'].rolling(window).max()
    df['liquidity_low'] = df['low'].rolling(window).min()
    return df

def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def calculate_macd(df):
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    return df

def calculate_lot_size(account_size, risk_percent, entry, sl):
    """حساب حجم اللوت"""
    risk_amount = account_size * (risk_percent / 100)
    sl_distance = abs(entry - sl)
    if sl_distance == 0:
        return 0
    lot_size = risk_amount / sl_distance
    return round(lot_size, 4)

def get_trade_signal(df):
    last = df.iloc[-1]
    signal = {'type': 'NEUTRAL', 'entry': None, 'sl': None, 'tp': None, 'reason': ''}
    if last.get('fvg_bullish', False) or last.get('ob_bullish', False) or last.get('bos_bullish', False):
        signal['type'] = 'BUY'
        signal['entry'] = last['close']
        signal['sl'] = last['liquidity_low']
        signal['tp'] = last['close'] + (last['close'] - last['liquidity_low']) * 2
        reasons = []
        if last.get('fvg_bullish', False): reasons.append('FVG')
        if last.get('ob_bullish', False): reasons.append('OB')
        if last.get('bos_bullish', False): reasons.append('BOS')
        signal['reason'] = ' + '.join(reasons)
    elif last.get('fvg_bearish', False) or last.get('ob_bearish', False) or last.get('bos_bearish', False):
        signal['type'] = 'SELL'
        signal['entry'] = last['close']
        signal['sl'] = last['liquidity_high']
        signal['tp'] = last['close'] - (last['liquidity_high'] - last['close']) * 2
        reasons = []
        if last.get('fvg_bearish', False): reasons.append('FVG')
        if last.get('ob_bearish', False): reasons.append('OB')
        if last.get('bos_bearish', False): reasons.append('BOS')
        signal['reason'] = ' + '.join(reasons)
    return signal

def get_mtf_analysis(symbol, timeframes=['15m', '1h', '4h']):
    """تحليل متعدد الأطر الزمنية"""
    results = {}
    for tf in timeframes:
        try:
            df = get_ohlcv(symbol, tf, 100)
            if df is not None:
                df = detect_swing_points(df)
                df = detect_fvg(df)
                df = detect_order_blocks(df)
                df = detect_liquidity(df)
                df = calculate_rsi(df)
                signal = get_trade_signal(df)
                results[tf] = {
                    'signal': signal['type'],
                    'rsi': round(df['rsi'].iloc[-1], 1),
                    'reason': signal['reason']
                }
        except:
            results[tf] = {'signal': 'N/A', 'rsi': 0, 'reason': ''}
    return results