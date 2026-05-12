class TradeManager:
    def __init__(self):
        self.trades = []
        self.balance = 10000

    def calculate_position_size(self, entry, sl, risk_percent=1):
        risk_amount = self.balance * (risk_percent / 100)
        sl_distance = abs(entry - sl)
        if sl_distance == 0:
            return 0
        position_size = risk_amount / sl_distance
        return round(position_size, 4)

    def open_trade(self, signal):
        if signal['type'] == 'NEUTRAL':
            return None
        size = self.calculate_position_size(signal['entry'], signal['sl'])
        trade = {
            'id': len(self.trades) + 1,
            'type': signal['type'],
            'entry': signal['entry'],
            'sl': signal['sl'],
            'tp': signal['tp'],
            'size': size,
            'status': 'OPEN',
            'pnl': 0,
            'rr_ratio': round(
                abs(signal['tp'] - signal['entry']) /
                abs(signal['sl'] - signal['entry']), 2
            )
        }
        self.trades.append(trade)
        return trade

    def update_trades(self, current_price):
        for trade in self.trades:
            if trade['status'] == 'OPEN':
                if trade['type'] == 'BUY':
                    trade['pnl'] = round(
                        (current_price - trade['entry']) * trade['size'], 2
                    )
                    if current_price >= trade['tp']:
                        trade['status'] = 'TP ✅'
                    elif current_price <= trade['sl']:
                        trade['status'] = 'SL ❌'
                else:
                    trade['pnl'] = round(
                        (trade['entry'] - current_price) * trade['size'], 2
                    )
                    if current_price <= trade['tp']:
                        trade['status'] = 'TP ✅'
                    elif current_price >= trade['sl']:
                        trade['status'] = 'SL ❌'
        return self.trades

    def get_stats(self):
        closed = [t for t in self.trades if t['status'] != 'OPEN']
        wins = [t for t in closed if t['pnl'] > 0]
        return {
            'total': len(self.trades),
            'open': len([t for t in self.trades if t['status'] == 'OPEN']),
            'closed': len(closed),
            'wins': len(wins),
            'winrate': round(len(wins)/len(closed)*100, 1) if closed else 0,
            'total_pnl': round(sum(t['pnl'] for t in self.trades), 2)
        }
    def save_to_csv(self):
        """حفظ الصفقات في ملف CSV"""
        import pandas as pd
        import os
        if self.trades:
            df = pd.DataFrame(self.trades)
            path = '/home/wail/trading_dashboard/data/trades.csv'
            df.to_csv(path, index=False)
            return path
        return None

    def load_from_csv(self):
        """تحميل الصفقات من ملف CSV"""
        import pandas as pd
        import os
        path = '/home/wail/trading_dashboard/data/trades.csv'
        if os.path.exists(path):
            df = pd.read_csv(path)
            self.trades = df.to_dict('records')