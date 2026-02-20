import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime
import math

# ==========================================
# 🎖️ 指揮部最高配置 (V8.C 3.1 核心邏輯導入)
# ==========================================
st.set_page_config(page_title="Trinity V3.1 指揮部", layout="wide")

TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  

@st.cache_data(ttl=300)
def fetch_market_data():
    try:
        # 為了 120MA，抓取 1 年數據
        df_0050 = yf.download("0050.TW", period="1y", interval="1d")
        df_2330 = yf.download("2330.TW", period="1mo", interval="1d")
        if df_0050.empty or df_2330.empty: return None

        if isinstance(df_0050.columns, pd.MultiIndex):
            df_0050.columns = df_0050.columns.get_level_values(0)
        if isinstance(df_2330.columns, pd.MultiIndex):
            df_2330.columns = df_2330.columns.get_level_values(0)

        close = float(df_0050['Close'].iloc[-1])
        ma20_series = df_0050['Close'].rolling(20).mean()
        ma20 = float(ma20_series.iloc[-1])
        ma20_prev = float(ma20_series.iloc[-2])
        
        # 規格書：120MA 與 突破位
        ma120 = float(df_0050['Close'].rolling(120).mean().iloc[-1])
        n20h = float(df_0050['High'].rolling(20).max().shift(1).iloc[-1])
        n10l = float(df_0050['Low'].rolling(10).min().shift(1).iloc[-1])
        bias = ((close - ma20) / ma20) * 100
        
        v_curr = float(df_2330['Volume'].iloc[-1])
        v5ma = float(df_2330['Volume'].rolling(5).mean().iloc[-1])
        v_ratio = v_curr / v5ma

        return {
            "price": close, "ma20": ma20, "ma20_prev": ma20_prev,
            "ma120": ma120, "n20h": n20h, "n10l": n10l,
            "bias": bias, "v_ratio": v_ratio, "v_curr": v_curr
        }
    except Exception as e:
        st.error(f"⚠️ 偵查受阻：{e}")
        return None

# ==========================================
# 🚀 執行主程序
# ==========================================

# --- 💰 側邊欄控制區 (首長原始介面) ---
st.sidebar.title("💰 戰術配置室")
capital = st.sidebar.number_input("總火種 (NTD)", value=30000, min_value=1000, step=10000)
entry_price = st.sidebar.number_input("第一梯隊進場價", value=0.0, step=0.1)

st.title("🎖️ Trinity V3.1 雲端指揮部")
st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

data = fetch_market_data()

if data:
    # 1. 規格書：火力分配判定
    c_val = data['price'] * 1000
    if capital < 100000:
        # 第一階段：6.0x 滿倉
        pos_35x = math.floor((capital * 6.0) / c_val)
        pos_60x = 0
        leverage_desc = "第一階段 6.0x"
    elif 100000 <= capital <= 3000000:
        # 第二階段：3.5x + 6.0x
        pos_35x = math.floor((capital * 0.5 * 3.5) / c_val)
        pos_60x = math.floor((capital * 0.5 * 6.0) / c_val)
        leverage_desc = "第二階段 3.5x+6.0x"
    else:
        # 第三階段：3.5x + 3.5x
        pos_35x = math.floor((capital * 0.5 * 3.5) / c_val)
        pos_60x = math.floor((capital * 0.5 * 3.5) / c_
