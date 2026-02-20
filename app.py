import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime
import math

# ==========================================
# 🎖️ 指揮部最高配置 - 嚴格執行規格書 3.1 邏輯
# ==========================================
st.set_page_config(page_title="Trinity V3.1 指揮部", layout="wide")

TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  

@st.cache_data(ttl=300)
def fetch_market_data():
    try:
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
        ma120 = float(df_0050['Close'].rolling(120).mean().iloc[-1])
        n20h = float(df_0050['High'].rolling(20).max().shift(1).iloc[-1])
        n10l = float(df_0050['Low'].rolling(10).min().shift(1).iloc[-1])
        bias = ((close - ma20) / ma20) * 100
        
        v_curr = float(df_2330['Volume'].iloc[-1])
        v_price = float(df_2330['Close'].iloc[-1])
        v5ma = float(df_2330['Volume'].rolling(5).mean().iloc[-1])
        v_ratio = v_curr / v5ma

        return {
            "price": close, "ma20": ma20, "ma20_prev": ma20_prev,
            "ma120": ma120, "n20h": n20h, "n10l": n10l,
            "bias": bias, "v_ratio": v_ratio, "v_curr": v_curr, "v_price": v_price
        }
    except Exception as e:
        st.error(f"⚠️ 偵查受阻：{e}")
        return None

# ==========================================
# 🚀 執行主程序
# ==========================================

# --- 💰 左側側邊欄 (槓桿保證金換算版) ---
st.sidebar.title("💰 戰術配置室")
capital = st.sidebar.number_input("總火種 (NTD)", value=30000, min_value=1000, step=10000)
entry_price_input = st.sidebar.number_input("第一梯隊進場價", value=0.0, step=0.1)

data = fetch_market_data()

if data:
    # 1. 戰術階段與基準保證金計算
    contract_value = data['price'] * 1000
    m_35x = contract_value / 3.5  # 3.5倍實質保證金
    m_60x = contract_value / 6.0  # 6.0倍實質保證金

    # 2. 兵力拆分邏輯
    if capital < 100000:
        # 第一階段：100% 資金跑 6.0x
        pos_35x = math.floor(capital / m_60x) 
        pos_60x = 0
        used_margin = pos_35x * m_60x
        tier1_label = "第一梯隊 (6.0x)"
    else:
        # 第二、三階段：50% 資金跑對應槓桿
        cap_split = capital * 0.5
        pos_35x = math.floor(cap_split / m_35x)
        if capital <= 3000000:
            pos_60x = math.floor(cap_split / m_60x)
        else:
            pos_60x = math.floor(cap_split / m_35x)
        used_margin = pos_35x * m_35x
        tier1_label = "第一梯隊 (3.5x)"
    
    total_pos = pos_35x + pos_60x
    remaining_margin = capital - used_margin

    # 3. 左側動態顯示 (100% 符合首長需求)
    st.sidebar.markdown(f"""
    <div style="background-color:#1e1e1e; padding:12px; border-radius:8px; border:1px solid #333; margin-top:10px;">
        <p style="color:#888; font-size:12
