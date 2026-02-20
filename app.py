import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime

# ==========================================
# 🎖️ 指揮部核心配置
# ==========================================
TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  
COMMAND_PASSWORD = "2836"  # 👈 請在此設定您的指揮官密碼

# --- 密碼驗證邏輯 ---
def check_password():
    """驗證密碼，成功則回傳 True"""
    def password_entered():
        if st.session_state["password"] == COMMAND_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 驗證後刪除，不留存於 session
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🎖️ Trinity 系統：身分驗證")
        st.text_input("請輸入指揮官授權密碼", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ 密碼錯誤，請重新輸入。")
        return False
    return st.session_state["password_correct"]

# --- 只有驗證成功才執行後續程式 ---
if check_password():

    # ==========================================
    # 📊 數據引擎 (更新為 5 分鐘刷新)
    # ==========================================
    @st.cache_data(ttl=300)  # 👈 已改為 300 秒 (5 分鐘)
    def fetch_market_data():
        try:
            df_0050 = yf.download("0050.TW", period="9mo", interval="1d")
            df_2330 = yf.download("2330.TW", period="1mo", interval="1d")
            
            if df_0050.empty or df_2330.empty: return None

            close = df_0050['Close'].iloc[-1]
            ma20 = df_0050['Close'].rolling(20).mean().iloc[-1]
            ma120 = df_0050['Close'].rolling(120).mean().iloc[-1]
            n20h = df_0050['High'].rolling(20).max().shift(1).iloc[-1]
            n10l = df_0050['Low'].rolling(10).min().shift(1).iloc[-1]
            bias = ((close - ma20) / ma20) * 100

            v_curr = df_2330['Volume'].iloc[-1]
            v5ma = df_2330['Volume'].rolling(5).mean().iloc[-1]
            v_ratio = v_curr / v5ma

            return {
                "price": close, "ma20": ma20, "ma120": ma120,
                "n20h": n20h, "n10l": n10l, "bias": bias,
                "v_ratio": v_ratio, "v5ma": v5ma, "v_curr": v_curr
            }
        except Exception as e:
            st.error(f"數據抓取失敗：{e}")
            return None

    # ==========================================
    # ⚡ 戰術分析邏輯
    # ==========================================
    def run_analysis(s):
        sig, act, color = "💤 靜默", "指標未達成共識", "info"
        is_climax_16 = s['v_ratio'] > 1.6

        # 多頭判斷
        if s['price'] > s['ma20'] and s['price'] >= s['n20h']:
            if s['v_ratio'] > 1.2 and s['bias'] <= 5.5:
                sig, act, color = "🔥 FIRE 多單點火", "買進 2 口小 0050 期 (3.5x)", "success"
            elif s['bias'] > 5.5:
                sig, act = "⚠️ 乖離過高", "禁止追多"

        # 空頭判斷
        elif s['price'] < s['ma20'] and s['price'] < s['ma120'] and s['price'] <= s['n10l']:
            if is_climax_16:
                sig, act, color = "🚫 禁止放空", "1.6x 爆量，禁止追空", "warning"
            elif s['v_ratio'] > 1.2:
                sig, act, color = "💣 ATTACK 空單突擊", "反手空單 (3.5x)", "error"

        # 出場
        if s['price'] < s['ma20']:
            sig, act, color = "🛑 RETREAT 多單撤退", "破 20MA 全數平倉", "error"
        if is_climax_16:
            sig += " | 🏳️ 空單熔斷"
            act += "\n【緊急】1.6x 爆量，空單平倉！"

        return sig, act, color

    # ==========================================
    # 🌐 Streamlit UI 介面
    # ==========================================
    st.set_page_config(page_title="Trinity V3.1 指揮部", layout="wide")
    st.title("🎖️ Trinity V3.1 雲端指揮部")
    st.caption(f"當前時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (偵察頻率：5 分鐘)")

    data = fetch_market_data()

    if data:
        sig, act, color = run_analysis(data)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("0050 目前價", f"{data['price']:.2f}")
        c2.metric("2330 量能比", f"{data['v_ratio']:.2f}x")
        c3.metric("20MA 乖離", f"{data['bias']:.2f}%")
        c4.metric("20日高點位", f"{data['n20h']:.2f}")

        st.divider()
        if color == "success": st.success(f"### 指令：{sig}")
        elif color == "warning": st.warning(f"### 指令：{
