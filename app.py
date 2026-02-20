import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. 權限驗證系統 ---
st.set_page_config(page_title="Trinity V3.2 密鑰指揮部", layout="wide")

# 這裡設定您的專屬密碼 (建議修改下方的 "1234")
MASTER_KEY = "2836" 

st.sidebar.title("🔐 安全驗證")
user_pwd = st.sidebar.text_input("輸入統帥授權碼", type="password")

if user_pwd != MASTER_KEY:
    st.title("🎖️ Trinity V3.2 雲端指揮部")
    st.warning("⚠️ 系統已鎖定。請於左側側邊欄輸入『統帥授權碼』以解除屏蔽。")
    st.info("副官提醒：未經授權禁止訪問戰略數據。")
    st.stop() # 密碼錯誤就直接切斷後續運算，保護數據

# --- 2. 核心邏輯 (驗證通過後才會執行) ---
st.title("🎖️ Trinity V3.2 雲端指揮部 [已授權]")

@st.cache_data(ttl=600)
def fetch_market_data():
    try:
        d050 = yf.download("0050.TW", period="1mo", auto_adjust=True, progress=False)
        d2330 = yf.download("2330.TW", period="1mo", auto_adjust=True, progress=False)
        
        if d050.empty or d2330.empty:
            return "數據真空，請稍後再試。"

        if isinstance(d050.columns, pd.MultiIndex):
            d050.columns = d050.columns.get_level_values(0)
        if isinstance(d2330.columns, pd.MultiIndex):
            d2330.columns = d2330.columns.get_level_values(0)
            
        p = float(d050['Close'].dropna().iloc[-1])
        m20 = float(d050['Close'].dropna().rolling(20).mean().iloc[-1])
        nh = float(d050['High'].dropna().rolling(20).max().shift(1).iloc[-1])
        v5ma = float(d2330['Volume'].dropna().tail(5).mean())
        curr_v = float(d2330['Volume'].dropna().iloc[-1])
        vr = curr_v / v5ma if v5ma > 0 else 0
        bias = ((p - m20) / m20) * 100
        
        return {"p": p, "m20": m20, "nh": nh, "vr": vr, "bias": bias}
    except Exception as e:
        return f"異常：{str(e)}"

# --- 3. 介面渲染 ---
st.sidebar.markdown("---")
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
