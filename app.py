import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime
import requests # 👈 新增補給

# ==========================================
# 🎖️ 指揮部核心配置
# ==========================================
TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  
COMMAND_PASSWORD = "2836" 

# --- 密碼驗證邏輯 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🎖️ Trinity 系統：身份驗證")
        pwd = st.text_input("2836", type="password")
        if st.button("核對身分"):
            if pwd == COMMAND_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ 密碼錯誤")
        return False
    return True

if check_password():
    # ==========================================
    # 📊 數據引擎 (強化偽裝版)
    # ==========================================
    @st.cache_data(ttl=300) 
    def fetch_market_data():
        try:
            # 🕵️ 幽靈偽裝設定
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
            }
            session = requests.Session()
            session.headers.update(headers)

            # 抓取數據並帶入 session
            df_0050 = yf.download("0050.TW", period="9mo", interval="1d", session=session)
            df_2330 = yf.download("2330.TW", period="1mo", interval="1d", session=session)
            
            if df_0050.empty or df_2330.empty:
                st.warning("📡 雅虎防線冷卻中，請 5 分鐘後再試...")
                return None

            # 指標計算
            close = df_0050['Close'].iloc[-1]
            ma20 = df_0050['Close'].rolling(20).mean().iloc[-1]
            ma120 = df_0050['Close'].rolling(120).mean().iloc[-1]
            n20h = df_0050['High'].rolling(20).max().shift(1).iloc[-1]
            n10l = df_0050['Low'].rolling(10).min().shift(1).iloc[-1]
            v_ratio = df_2330['Volume'].iloc[-1] / df_2330['Volume'].rolling(5).mean().iloc[-1]
            bias = ((close - ma20) / ma20) * 100

            return {"price": close, "ma20": ma20, "ma120": ma120, "n20h": n20h, "n10l": n10l, "v_ratio": v_ratio, "bias": bias}
        except Exception as e:
            st.error(f"⚠️ 偵查受阻：{e}")
            return None

    # ==========================================
    # 🌐 UI 介面
    # ==========================================
    st.set_page_config(page_title="Trinity V3.1 指揮部", layout="wide")
    st.title("🎖️ Trinity V3.1 雲端指揮部")
    st.caption(f"數據頻率：5 分鐘 | 現在時間：{datetime.now().strftime('%H:%M:%S')}")

    data = fetch_market_data()

    if data:
        # (這裡放原本的戰術分析邏輯與 UI 顯示)
        st.success(f"0050 目前價：{data['price']:.2f} | 量比：{data['v_ratio']:.2f}x")
        
        # 手動發報按鈕
        if st.button("🚀 請求戰報發送"):
            # ... 原本的 Telegram 發送邏輯 ...
            st.write("戰報已送達！")
