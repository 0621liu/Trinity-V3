import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Trinity V3.1 絕對指揮部", layout="wide")
st.title("🎖️ Trinity V3.1 雲端指揮部 [絕對防禦版]")

@st.cache_data(ttl=600)
def fetch_market_data():
    try:
        # 抓取稍長一點的區間確保一定有資料
        d050 = yf.download("0050.TW", period="1mo", auto_adjust=True, progress=False)
        d2330 = yf.download("2330.TW", period="1mo", auto_adjust=True, progress=False)
        
        if d050.empty or d2330.empty:
            return "目前抓不到市場數據，請確認網路或是否為非交易時段。"

        if isinstance(d050.columns, pd.MultiIndex):
            d050.columns = d050.columns.get_level_values(0)
        if isinstance(d2330.columns, pd.MultiIndex):
            d2330.columns = d2330.columns.get_level_values(0)
            
        # --- 防踩空邏輯：確保取到最後一個非空值 ---
        p = float(d050['Close'].dropna().iloc[-1])
        m20 = float(d050['Close'].dropna().rolling(20).mean().iloc[-1])
        nh = float(d050['High'].dropna().rolling(20).max().shift(1).iloc[-1])
        
        v_series = d2330['Volume'].dropna()
        v5ma = float(v_series.tail(5).mean())
        curr_v = float(v_series.iloc[-1])
        vr = curr_v / v5ma if v5ma > 0 else 0
        
        bias = ((p - m20) / m20) * 100
        
        return {"p": p, "m20": m20, "nh": nh, "vr": vr, "bias": bias}
    except Exception as e:
        return f"數據分析異常：{str(e)}"

# --- 介面渲染 ---
capital = st.sidebar.number_input("當前總資產 (TWD)", value=30000, step=1000)
res = fetch_market_data()

if isinstance(res, dict):
    c1, c2, c3 = st.columns(3)
    c1.metric("0050 現價", f"{res['p']:.2f}", f"{res['p']-res['m20']:.2f}")
    c2.metric("2330 量能比", f"{res['vr']:.2f}x", "門檻 1.20x")
    c3.metric("乖離率", f"{res['bias']:.1f}%", "上限 5.5%")

    is_trend = res['p'] > res['m20'] and res['p'] >= res['nh']
    is_vol = res['vr'] >= 1.2
    is_safe = res['bias'] <= 5.5

    st.markdown("---")
    if is_trend and is_vol and is_safe:
        st.success("🔥 [FIRE] 符合 V3.1 點火條件！")
    elif res['p'] < res['m20']:
        st.error("🛑 [RETREAT] 價格破月線，撤退。")
    else:
        st.warning("💤 [WAIT] 指標未全亮，保持靜默。")

    lev = 6.0 if capital < 100000 else (3.5 if capital >= 3000000 else 4.75)
    lots = (capital * lev) / (res['p'] * 1000)
    st.subheader(f"⚔️ 彈藥建議 (槓桿: {lev}x)")
    st.write(f"當前建議持有: **{round(lots, 1)} 口**")
else:
    st.error(res)
