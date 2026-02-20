import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime
import requests

# ==========================================
# 🎖️ 指揮部核心配置 (請務必修改此處)
# ==========================================
TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  
COMMAND_PASSWORD = "2836" # 👈 這是登入網頁的密碼

# ==========================================
# 🛡️ 權限驗證系統
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🎖️ Trinity 系統：身份驗證")
        st.caption("本系統受加密保護，請輸入授權密碼以進入指揮部。")
        pwd = st.text_input("授權密碼", type="password")
        if st.button("登入系統"):
            if pwd == COMMAND_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ 密碼錯誤，拒絕訪問。")
        return False
    return True

# ==========================================
# 📊 數據引擎 (具備 User-Agent 偽裝與 5 分鐘刷新)
# ==========================================
@st.cache_data(ttl=300) # 每 300 秒 (5 分鐘) 刷新一次
def fetch_market_data():
    try:
        # --- 建立偽裝 Session 避開 Yahoo 封鎖 ---
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        session = requests.Session()
        session.headers.update(headers)

        # 抓取數據 (0050 & 2330)
        df_0050 = yf.download("0050.TW", period="9mo", interval="1d", session=session)
        df_2330 = yf.download("2330.TW", period="1mo", interval="1d", session=session)
        
        if df_0050.empty or df_2330.empty: return None

        # 計算指標
        close = df_0050['Close'].iloc[-1]
        ma20 = df_0050['Close'].rolling(20).mean().iloc[-1]
        ma120 = df_0050['Close'].rolling(120).mean().iloc[-1]
        n
