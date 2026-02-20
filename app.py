import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime
import math

# ==========================================
# 🎖️ 指揮部最高配置
# ==========================================
st.set_page_config(page_title="Trinity V3.1 指揮部", layout="wide")

TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  

# ==========================================
# 📊 數據偵查引擎
# ==========================================
@st.cache_data(ttl=300)
def fetch_market_data():
    try:
        df_0050 = yf.download("0050.TW", period="9mo", interval="1d")
        df_2330 = yf.download("2330.TW", period="1mo", interval="1d")
        
        if df_0050.empty or df_2330.empty: return None

        # 修正 MultiIndex
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
        v5ma = float(df_2330['Volume'].rolling(5).mean().iloc[-1])
        v_ratio = v_curr / v5ma

        return {
            "price": close, "ma20": ma20, "ma20_prev": ma20_prev,
            "ma120": ma120, "n20h": n20h, "n10l": n10l,
            "bias": bias, "v_ratio": v_ratio
        }
    except Exception as e:
        st.error(f"⚠️ 偵查受阻：{e}")
        return None

# ==========================================
# 🚀 執行主程序 (無密碼版)
# ==========================================
st.sidebar.title("💰 資金調度室")
capital = st.sidebar.number_input("總預算 (NTD)", value=1000000, step=100000)
st.sidebar.divider()
st.sidebar.write("**🎯 小 0050 期規格**")
st.sidebar.write("- 1 點 = 1,000 NTD")
st.sidebar.write("- 原始保證金 = 4,200 NTD")

st.title("🎖️ Trinity V3.1 雲端指揮部")
st.caption(f"偵查頻率：5 分鐘 | 現在時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

data = fetch_market_data()

if data:
    # 1. 換算邏輯
    contract_value = data['price'] * 1000
    pos_35x = math.floor((capital * 3.5) / contract_value)
    pos_60x = math.floor((capital * 6.0) / contract_value)
    
    # 2. 趨勢判定
    is_ma20_down = data['ma20'] < data['ma20_prev']
    is_ma20_up = data['ma20'] > data['ma20_prev']
    is_climax_16 = data['v_ratio'] > 1.6

    # 3. 戰術分析
    sig, act, color, target_pos = "💤 靜默", "等待指標共振", "info", 0

    # 多頭判定
    if data['price'] > data['ma20'] and is_ma20_up and data['price'] >= data['n20h']:
        if data['v_ratio'] > 1.2 and data['bias'] <= 5.5:
            sig, act, color = "🔥 FIRE 多單點火", f"建議建立 {pos_35x} 口，獲利 >2% 後加碼至 {pos_60x} 口", "success"
            target_pos = pos_35x
        elif data['bias'] > 5.5:
            sig, act = "⚠️ 乖離過高", "禁止追多，等待回踩月線"
    
    # 空頭判定 (修正第 104 行 Syntax)
    elif data['price'] < data['ma20'] and data['price'] < data['ma120'] and data['price'] <= data['n10l']:
        if is_climax_16:
            sig, act, color = "🚫 禁止放空", "台積電 1.6x 爆量避險，禁止追空", "warning"
        elif is_ma20_down and data['v_ratio'] > 1.2:
            sig, act, color = "💣 ATTACK 空單突擊", f"反手建立 {pos_35x} 口空單", "error"
            target_pos = pos_35x
        elif not is_ma20_down:
            sig, act = "⏳ 等待月線下彎", "價格已破位，但月線斜率尚未轉負"

    # 出場邏輯
    if data['price'] < data['ma20']:
        sig, act, color = "🛑 RETREAT 撤退", "跌破 20MA 全數平倉", "error"
    if is_climax_16:
        sig += " | 🏳️ 空單熔斷"
        act += "\n【警報】1.6x 爆量，空單立即平倉！"

    # 4. 面板顯示
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("小0050 建議口數", f"{pos_35x} / {pos_60x}")
    c2.metric("台積電量比", f"{data['v_ratio']:.2f}x")
    c3.
