import pandas as pd
import numpy as np

def run_backtest(df, initial_balance=10000, risk_percent=1):
    balance = initial_balance
    trades = []
    wins = 0
    losses = 0

    for i in range(10, len(df)-1):
        slice_df = df.iloc[:i].copy()
        last = slice_df.iloc[-1]

        if last.get('fvg_bullish', False):
            entry = last['close']
            sl = last['liquidity_low']
            tp = entry + (entry - sl) * 2
            risk = balance * (risk_percent / 100)
            size = risk / abs(entry - sl) if abs(entry - sl) > 0 else 0

            future = df.iloc[i:i+20]
            result = 'OPEN'
            pnl = 0

            for _, candle in future.iterrows():
                if candle['high'] >= tp:
                    result = 'WIN'
                    pnl = round(size * (tp - entry), 2)
                    wins += 1
                    break
                elif candle['low'] <= sl:
                    result = 'LOSS'
                    pnl = round(size * (sl - entry), 2)
                    losses += 1
                    break

            if result != 'OPEN':
                balance += pnl
                trades.append({
                    'type': 'BUY',
                    'entry': round(entry, 2),
                    'sl': round(sl, 2),
                    'tp': round(tp, 2),
                    'result': result,
                    'pnl': pnl,
                    'balance': round(balance, 2)
                })

    total = wins + losses
    winrate = round(wins/total*100, 1) if total > 0 else 0
    profit = round(balance - initial_balance, 2)

    return {
        'trades': trades[-20:],
        'total': total,
        'wins': wins,
        'losses': losses,
        'winrate': winrate,
        'final_balance': round(balance, 2),
        'profit': profit
    }