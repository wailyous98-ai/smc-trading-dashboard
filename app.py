import sys
import time
sys.path.insert(0, '/home/wail/trading_dashboard')
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from src.data_fetcher import get_ohlcv, get_current_price
from src.smc_analyzer import detect_swing_points, detect_bos_choch, detect_order_blocks, detect_fvg, detect_liquidity, get_trade_signal, calculate_rsi, calculate_macd, calculate_lot_size, get_mtf_analysis
from src.trade_manager import TradeManager
from src.alerts import get_crypto_news
from src.auth import create_auth
from src.languages import get_text, LANGUAGES
from src.firebase_auth import verify_license

st.set_page_config(page_title="SMC Trading Dashboard", page_icon="icon.png", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: radial-gradient(ellipse at 20% 50%, #1a0533 0%, #0a0010 50%, #000208 100%); }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0d0020, #050010) !important; border-right: 1px solid #7b2fff30 !important; }
h1,h2,h3 { font-family: 'Orbitron', sans-serif !important; color: #00d4ff !important; }
.stButton > button { background: linear-gradient(135deg, #7b2fff, #00d4ff) !important; border: none !important; border-radius: 10px !important; color: white !important; font-weight: 700 !important; }
div[data-testid="stMetricValue"] { color: #00d4ff !important; font-family: 'Orbitron', sans-serif !important; }
.signal-buy { background: linear-gradient(135deg, #003d1a, #005c27); border: 2px solid #00ff88; border-radius: 12px; padding: 20px; text-align: center; font-size: 24px; font-weight: 700; color: #00ff88; }
.signal-sell { background: linear-gradient(135deg, #3d0000, #5c0000); border: 2px solid #ff4444; border-radius: 12px; padding: 20px; text-align: center; font-size: 24px; font-weight: 700; color: #ff4444; }
.signal-neutral { background: linear-gradient(135deg, #1a1f2e, #16213e); border: 2px solid #888; border-radius: 12px; padding: 20px; text-align: center; font-size: 20px; color: #888; }
div[data-testid="stForm"] { background: linear-gradient(135deg, rgba(123,47,255,0.2), rgba(0,10,30,0.95)) !important; border: 1px solid rgba(123,47,255,0.6) !important; border-radius: 20px !important; padding: 30px !important; box-shadow: 0 0 60px rgba(123,47,255,0.3) !important; }
div[data-testid="stForm"] input { background: rgba(0,0,0,0.5) !important; border: 1px solid rgba(123,47,255,0.4) !important; border-radius: 10px !important; color: white !important; }
.disclaimer { background: rgba(255,200,0,0.1); border: 1px solid rgba(255,200,0,0.3); border-radius: 10px; padding: 12px; font-size: 12px; color: #ffd700; margin: 10px 0; }
.license-active { background: rgba(0,255,136,0.1); border: 1px solid #00ff88; border-radius: 8px; padding: 8px; color: #00ff88; text-align: center; }
.license-inactive { background: rgba(255,68,68,0.1); border: 1px solid #ff4444; border-radius: 8px; padding: 8px; color: #ff4444; text-align: center; }
.mtf-card { background: #1a1f2e; border: 1px solid #ffffff15; border-radius: 10px; padding: 12px; text-align: center; margin: 4px; }
</style>
""", unsafe_allow_html=True)

# ========== Auth ==========
authenticator = create_auth()
authenticator.login(location="main")
name = st.session_state.get("name")
authentication_status = st.session_state.get("authentication_status")

if authentication_status == False:
    st.error("Username or password incorrect")
    st.stop()
elif authentication_status is None:
    st.markdown("""
    <div style='text-align:center; padding:60px 0 30px 0;'>
        <div style='font-family:Orbitron,sans-serif; font-size:48px; font-weight:900;
            background:linear-gradient(135deg,#7b2fff,#00d4ff);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
            margin-bottom:10px;'>📈 SMC TRADER</div>
        <div style='color:#8892a4; font-size:11px; letter-spacing:6px;'>SMART MONEY CONCEPTS — PRO EDITION</div>
        <div style='width:80px; height:2px; background:linear-gradient(90deg,#7b2fff,#00d4ff); margin:20px auto;'></div>
                <div style='background:rgba(255,200,0,0.1);border:1px solid rgba(255,200,0,0.4);border-radius:12px;padding:16px;margin:10px auto;max-width:500px;text-align:center;'>
        <div style='color:#ffd700;font-size:13px;font-weight:700;'>⚠️ DISCLAIMER</div>
        <div style='color:#a0aec0;font-size:11px;margin-top:8px;'>This tool is for educational purposes only. Not financial advice. Developer: Wail</div>
    </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ========== Sidebar ==========
with st.sidebar:
    authenticator.logout("Logout", "sidebar")
    st.write(f"👤 **{name}**")
    st.markdown("---")

    lang = st.selectbox(get_text('English', 'language'), list(LANGUAGES.keys()))
    T = lambda key: get_text(lang, key)

    st.markdown("---")
    st.markdown(f"## {T('settings')}")

    # License Verification
    st.markdown(f"### 🔐 {T('license')}")
    email_input = st.text_input(T('email'), placeholder="email@example.com")
    license_input = st.text_input(T('license'), placeholder="SMC-PRO-XXXX", type="password")

    if st.button(T('verify'), use_container_width=True):
        if email_input and license_input:
            result = verify_license(email_input, license_input)
            if result['success']:
                st.session_state['license_verified'] = True
                st.session_state['user_plan'] = result['plan']
                st.success(f"✅ {result['plan']} Plan Active")
            else:
                st.session_state['license_verified'] = False
                st.error(f"❌ {result['message']}")
        else:
            st.warning("Please enter email and license key")

    license_verified = st.session_state.get('license_verified', False)
    user_plan = st.session_state.get('user_plan', 'Free')

    if license_verified:
        st.markdown(f"<div class='license-active'>✅ {T('active')} — {user_plan}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='license-inactive'>⚠️ {T('inactive')}</div>", unsafe_allow_html=True)

    st.markdown("---")

    category = st.selectbox(T('category'), ['Bitcoin & Crypto', 'Altcoins'])
    if category == 'Bitcoin & Crypto':
        symbol = st.selectbox(T('pair'), ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'])
    else:
        symbol = st.selectbox(T('pair'), ['SOL/USDT', 'XRP/USDT', 'EUR/USDT'])

    timeframe = st.selectbox(T('timeframe'), ['15m', '1h', '4h', '1d'])
    risk = st.slider(T('risk'), 0.5, 5.0, 1.0, 0.5)
    account_size = st.number_input(T('account_size'), min_value=100, value=10000, step=100)

    st.markdown("---")
    st.markdown("**System:** SMC / ICT")
    st.markdown("**Exchange:** Binance")
    st.markdown("**Version:** v3.0 Pro")
    st.markdown("---")
    if st.button(T('refresh'), use_container_width=True):
        st.rerun()

# ========== Header ==========
st.markdown(f"# 📈 {T('title')}")
st.markdown("---")

# ========== Disclaimer ==========
st.markdown(f"<div class='disclaimer'>{T('disclaimer')}</div>", unsafe_allow_html=True)

# ========== Data ==========
with st.spinner(""):
    price_data = get_current_price(symbol)
    df = get_ohlcv(symbol, timeframe, 200)

if df is None or df.empty:
    st.error("Failed to load data")
    st.stop()

df = detect_swing_points(df)
df = detect_fvg(df)
df = detect_order_blocks(df)
df = detect_bos_choch(df)
df = detect_liquidity(df)
df = calculate_rsi(df)
df = calculate_macd(df)
signal = get_trade_signal(df)

# ========== Price ==========
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(T('price'), f"${price_data['price']:,.0f}")
with c2:
    st.metric(T('high'), f"${price_data['high_24h']:,.2f}")
with c3:
    st.metric(T('low'), f"${price_data['low_24h']:,.0f}")
with c4:
    st.metric(T('change'), f"{price_data['change_24h']:.2f}%")

st.markdown("---")

# ========== Signal ==========
col_sig, col_levels = st.columns([1, 2])

with col_sig:
    st.markdown(f"### {T('signal')}")
    if signal['type'] == 'BUY':
        st.markdown(f"<div class='signal-buy'>✅ {T('buy')}</div>", unsafe_allow_html=True)
    elif signal['type'] == 'SELL':
        st.markdown(f"<div class='signal-sell'>🔴 {T('sell')}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='signal-neutral'>⏳ {T('neutral')}</div>", unsafe_allow_html=True)

    if signal.get('reason'):
        st.markdown(f"**Reason:** `{signal['reason']}`")

    rsi_val = df['rsi'].iloc[-1]
    macd_val = df['macd'].iloc[-1]
    st.metric("RSI", f"{rsi_val:.1f}")
    st.metric("MACD", f"{macd_val:.2f}")

with col_levels:
    st.markdown(f"### {T('trade_levels')}")
    if signal['entry'] and license_verified:
        lot = calculate_lot_size(account_size, risk, signal['entry'], signal['sl'])
        st.markdown(f"""
        <div style='display:flex; gap:10px; margin-top:10px; flex-wrap:wrap;'>
            <div style='flex:1; min-width:120px; background:#0d1117; border:1px solid #7b2fff40; border-radius:12px; padding:16px; text-align:center;'>
                <div style='color:#8892a4; font-size:11px; letter-spacing:2px;'>{T('entry')}</div>
                <div style='color:#00d4ff; font-size:18px; font-weight:700; margin-top:6px;'>${signal['entry']:,.2f}</div>
            </div>
            <div style='flex:1; min-width:120px; background:#0d1117; border:1px solid #ff444440; border-radius:12px; padding:16px; text-align:center;'>
                <div style='color:#8892a4; font-size:11px; letter-spacing:2px;'>{T('sl')}</div>
                <div style='color:#ff4444; font-size:18px; font-weight:700; margin-top:6px;'>${signal['sl']:,.2f}</div>
            </div>
            <div style='flex:1; min-width:120px; background:#0d1117; border:1px solid #00ff8840; border-radius:12px; padding:16px; text-align:center;'>
                <div style='color:#8892a4; font-size:11px; letter-spacing:2px;'>{T('tp')}</div>
                <div style='color:#00ff88; font-size:18px; font-weight:700; margin-top:6px;'>${signal['tp']:,.2f}</div>
            </div>
            <div style='flex:1; min-width:120px; background:#0d1117; border:1px solid #ffd70040; border-radius:12px; padding:16px; text-align:center;'>
                <div style='color:#8892a4; font-size:11px; letter-spacing:2px;'>{T('lot_size')}</div>
                <div style='color:#ffd700; font-size:18px; font-weight:700; margin-top:6px;'>{lot}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif not license_verified:
        st.warning("🔐 Please verify your license to see trade levels")
    else:
        st.info("Waiting for signal...")

st.markdown("---")

# ========== MTF Analysis ==========
st.markdown(f"### 📊 {T('mtf')}")
if license_verified:
    with st.spinner("Loading MTF..."):
        mtf = get_mtf_analysis(symbol, ['15m', '1h', '4h'])
    cols = st.columns(len(mtf))
    for i, (tf, data) in enumerate(mtf.items()):
        with cols[i]:
            color = '#00ff88' if data['signal'] == 'BUY' else '#ff4444' if data['signal'] == 'SELL' else '#888'
            st.markdown(f"""
            <div class='mtf-card'>
                <div style='color:#8892a4; font-size:12px;'>{tf}</div>
                <div style='color:{color}; font-size:20px; font-weight:700;'>{data['signal']}</div>
                <div style='color:#8892a4; font-size:11px;'>RSI: {data['rsi']}</div>
                <div style='color:#7b2fff; font-size:10px;'>{data['reason']}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.warning("🔐 License required for MTF Analysis")

st.markdown("---")

# ========== Chart ==========
st.markdown(f"### {T('chart')}")
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])
fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name=symbol, increasing_line_color='#00ff88', decreasing_line_color='#ff4444'), row=1, col=1)

# FVG zones
fvg_bull = df[df['fvg_bullish'] == True].tail(3)
fvg_bear = df[df['fvg_bearish'] == True].tail(3)
for idx, row in fvg_bull.iterrows():
    fig.add_hrect(y0=row['fvg_bottom'], y1=row['fvg_top'], fillcolor='rgba(0,255,136,0.1)', line_width=0, row=1, col=1)
for idx, row in fvg_bear.iterrows():
    fig.add_hrect(y0=row['fvg_bottom'], y1=row['fvg_top'], fillcolor='rgba(255,68,68,0.1)', line_width=0, row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], line=dict(color='#00d4ff', width=1.5), name='RSI'), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="#ff4444", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="#00ff88", row=2, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['macd'], line=dict(color='#00d4ff', width=1.5), name='MACD'), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], line=dict(color='#ff9500', width=1.5), name='Signal'), row=3, col=1)
fig.add_trace(go.Bar(x=df.index, y=df['macd_hist'], name='Hist', marker_color=['#00ff88' if v > 0 else '#ff4444' for v in df['macd_hist']]), row=3, col=1)

fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(13,5,30,0.8)', height=600, showlegend=True, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=10, b=0), hovermode='x unified', hoverlabel=dict(bgcolor='#1a0533', bordercolor='#7b2fff', font=dict(color='white')))
fig.update_xaxes(gridcolor='#1a1a2e')
fig.update_yaxes(gridcolor='#1a1a2e')

chart_placeholder = st.empty()
chart_placeholder.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ========== Trade Manager ==========
st.markdown(f"### {T('trade_manager')}")
if 'trade_manager' not in st.session_state:
    st.session_state.trade_manager = TradeManager()

tm = st.session_state.trade_manager
tm.update_trades(price_data['price'])
stats = tm.get_stats()

t1, t2, t3, t4 = st.columns(4)
t1.metric(T('total'), stats['total'])
t2.metric(T('open'), stats['open'])
t3.metric(T('win_rate'), f"{stats['winrate']}%")
t4.metric(T('pnl'), f"${stats['total_pnl']}")

col_a, col_b, col_c = st.columns(3)
with col_a:
    if st.button(T('open_trade'), use_container_width=True, key="btn_open"):
        if license_verified:
            trade = tm.open_trade(signal)
            if trade:
                st.success("Trade opened!")
            else:
                st.warning("No signal")
        else:
            st.error("License required")
with col_b:
    if st.button(T('save_csv'), use_container_width=True, key="btn_save"):
        path = tm.save_to_csv()
        if path:
            st.success("Saved!")
        else:
            st.warning("No trades")
with col_c:
    if st.button(T('close_all'), use_container_width=True, key="btn_close"):
        for trade in tm.trades:
            if trade['status'] == 'OPEN':
                trade['status'] = 'CLOSED'
                trade['pnl'] = round((price_data['price'] - trade['entry']) * trade['size'], 2) if trade['type'] == 'BUY' else round((trade['entry'] - price_data['price']) * trade['size'], 2)
        st.success("All closed!")

if tm.trades:
    df_trades = pd.DataFrame(tm.trades)
    st.dataframe(df_trades[['id','type','entry','sl','tp','size','rr_ratio','status','pnl']], use_container_width=True)

st.markdown("---")

# ========== News ==========
st.markdown(f"### 📰 {T('news')}")
col_n1, col_n2, col_n3 = st.columns(3)
with col_n1:
    st.link_button("📰 CoinDesk", "https://www.coindesk.com", use_container_width=True)
with col_n2:
    st.link_button("📊 CryptoSlate", "https://cryptoslate.com", use_container_width=True)
with col_n3:
    st.link_button("🌍 Investing.com", "https://www.investing.com/news/cryptocurrency-news", use_container_width=True)

st.markdown("---")

# ========== Backtesting ==========
st.markdown(f"### 🧪 {T('backtest')}")
if st.button(T('run_backtest'), use_container_width=True, key="btn_backtest"):
    if license_verified:
        from src.backtesting import run_backtest
        with st.spinner("Running..."):
            results = run_backtest(df)
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Total Trades", results['total'])
        b2.metric("Win Rate", f"{results['winrate']}%")
        b3.metric("Final Balance", f"${results['final_balance']:,.2f}")
        b4.metric("Profit", f"${results['profit']:,.2f}")
        if results['trades']:
            st.dataframe(pd.DataFrame(results['trades']), use_container_width=True)
    else:
        st.error("🔐 License requi[red for Backtesting")

time.sleep(5)
st.rerun(scope="fragment")
