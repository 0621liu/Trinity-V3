import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime
import requests

# ==========================================
# 🎖️ 指揮部最高配置 (請在此修改您的私人資訊)
# ==========================================
TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  # 找 @userinfobot 取得數字 ID
COMMAND_PASSWORD = "2836" # 👈 登入網頁用

# ==========================================
# 🛡️ 安全驗證模組
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🎖️ Trinity 系統：身份驗證")
        st.caption("本系統受加密保護，非授權統帥禁止進入。")
        pwd = st.text_input("2836", type="password")
        if st.button("核對身分"):
            if pwd == COMMAND_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ 密碼錯誤，拒絕訪問。")
        return False
    return True

# ==========================================
# 📊 數據偵查引擎 (5分鐘刷新 + 偽裝網)
# ==========================================
@st.cache_data(ttl=300)
def fetch_market_data():
    try:
        # 使用 Session 偽裝成一般瀏覽器，避免被 Yahoo 封鎖
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0 Safari/537.36'}
        session = requests.Session()
        session.headers.update(headers)

        # 抓取數據 (0050 與 2330)
        df_0050 = yf.download("0050.TW", period="9mo", interval="1d", session=session)
        df_2330 = yf.download("2330.TW", period="1mo", interval="1d", session=session)
        
        # 🛡️ 容錯檢查：確保數據非空且長度足夠
        if df_0050.empty or df_2330.empty:
            return None
        if len(df_0050) < 21:
            return "DATA_INSUFFICIENT"

        # 計算指標
        close = df_0050['Close'].iloc[-1]
        ma20 = df_0050['Close'].rolling(20).mean().iloc[-1]
        ma120 = df_0050['Close'].rolling(120).mean().iloc[-1]
        n20h = df_0050['High'].rolling(20).max().shift(1).iloc[-1]
        n10l = df_0050['Low'].rolling(10).min().shift(1).iloc[-1]
        bias = ((close - ma20) / ma20) * 100

        # 台積電量能比
        v_curr = df_2330['Volume'].iloc[-1]
        v5ma = df_2330['Volume'].rolling(5).mean().iloc[-1]
        v_ratio = v_curr / v5ma

        return {
            "price": close, "ma20": ma20, "ma120": ma120,
            "n20h": n20h, "n10l": n10l, "bias": bias,
            "v_ratio": v_ratio
        }
    except Exception as e:
        st.error(f"⚠️ 雅虎連線受困：{e}")
        return None

# ==========================================
# ⚡ 戰術分析邏輯 (V3.1 最終校準)
# ==========================================
def run_tactics(s):
    sig, act, color = "💤 靜默", "等待指標共振", "info"
    is_climax_16 = s['v_ratio'] > 1.6

    # 1. 多頭判定 (Long)
    if s['price'] > s['ma20'] and s['price'] >= s['n20h']:
        if s['v_ratio'] > 1.2 and s['bias'] <= 5.5:
            sig, act, color = "🔥 FIRE 多單點火", "買進 2 口小 0050 期 (3.5x)\n獲利 >2% 後加碼至 3 口 (6.0x)", "success"
        elif s['bias'] > 5.5:
            sig, act = "⚠️ 乖離過高", "目前位置不宜進場，等待月線回靠"

   # --- 修正後的空頭判定區塊 ---
        elif data['price'] < data['ma20'] and data['price'] < data['ma120'] and data['price'] <= data['n10l']:
            if is_climax_16:
                sig, act, color = "🚫 禁止放空", "台積電 1.6x 爆量，疑有護盤，禁止追空", "warning"
            elif data['v_ratio'] > 1.2:
                sig, act, color = "💣 ATTACK 空單突擊", "反手放空 2 口小 0050 期 (3.5x)", "error"
