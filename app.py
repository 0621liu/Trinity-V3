import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime

# ==========================================
# 🎖️ 指揮部核心配置 (請填寫您的資訊)
# ==========================================
TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  # 找 @userinfobot 取得

# ==========================================
# 📊 數據引擎 (具備快取機制，避免被封鎖)
# ==========================================
@st.cache_data(ttl=900)  # 每 15 分鐘刷新一次數據
def fetch_market_data():
    try:
        # 抓取 0050 (趨勢) 與 2330 (動能)
        df_0050 = yf.download("0050.TW", period="9mo", interval="1d")
        df_2330 = yf.download("2330.TW", period="1mo", interval="1d")
        
        if df_0050.empty or df_tsmc.empty: return None

        # 1. 0050 價格指標
        close = df_0050['Close'].iloc[-1]
        ma20 = df_0050['Close'].rolling(20).mean().iloc[-1]
        ma120 = df_0050['Close'].rolling(120).mean().iloc[-1]
        n20h = df_0050['High'].rolling(20).max().shift(1).iloc[-1]
        n10l = df_0050['Low'].rolling(10).min().shift(1).iloc[-1]
        bias = ((close - ma20) / ma20) * 100

        # 2. 2330 量能指標 (1.2x 進場, 1.6x 空頭熔斷)
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
    sig = "💤 靜默"
    act = "指標未達成共識，保持觀望"
    status_color = "info"
    
    is_climax_16 = s['v_ratio'] > 1.6

    # --- 多頭判斷 (Long) ---
    if s['price'] > s['ma20'] and s['price'] >= s['n20h']:
        if s['v_ratio'] > 1.2 and s['bias'] <= 5.5:
            sig, act, status_color = "🔥 FIRE 多單點火", "買進 2 口小 0050 期 (3.5x)\n獲利 >2% 加碼至 3 口 (6.0x)", "success"
        elif s['bias'] > 5.5:
            sig, act = "⚠️ 乖離過高", "等待回踩月線，禁止追高"

    # --- 空頭判斷 (Short) ---
    elif s['price'] < s['ma20'] and s['price'] < s['ma120'] and s['price'] <= s['n10l']:
        if is_climax_16:
            sig, act, status_color = "🚫 禁止放空", "台積電 1.6x 爆量，疑有護盤，禁止追空", "warning"
        elif s['v_ratio'] > 1.2:
            sig, act, status_color = "💣 ATTACK 空單突擊", "反手點火空單 (3.5x)", "error"

    # --- 出場邏輯 ---
    if s['price'] < s['ma20']:
        sig, act, status_color = "🛑 RETREAT 多單撤退", "跌破 20MA，多單全數平倉", "error"
    
    if is_climax_16: # 針對空頭的 1.6x 無條件出場
        # 注意：此處邏輯假設若首長持有空單則觸發
        sig = sig + " | 🏳️ 空單熔斷"
        act = act + "\n【緊急】空頭遭遇 1.6x 爆量，空單無條件平倉！"

    return sig, act, status_color

# ==========================================
# 🌐 Streamlit UI 介面
# ==========================================
st.set_page_config(page_title="Trinity V3.1 指揮部", layout="wide")
st.title("🎖️ Trinity V3.1 雲端指揮部")
st.caption(f"當前時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (市場數據每 15 分鐘刷新)")

data = fetch_market_data()

if data:
    sig, act, color = run_analysis(data)

    # 儀表板
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("0050 目前價", f"{data['price']:.2f}")
    c2.metric("2330 量能比", f"{data['v_ratio']:.2f}x")
    c3.metric("20MA 乖離", f"{data['bias']:.2f}%")
    c4.metric("20日高點位", f"{data['n20h']:.2f}")

    st.divider()

    # 戰術顯示
    if color == "success": st.success(f"### 指令：{sig}")
    elif color == "warning": st.warning(f"### 指令：{sig}")
    elif color == "error": st.error(f"### 指令：{sig}")
    else: st.info(f"### 指令：{sig}")

    st.write(f"**戰術動作：**\n{act}")

    # ==========================================
    # 📢 手動通訊區 (靜默模式)
    # ==========================================
    st.divider()
    st.subheader("📢 戰訊發送控制")
    st.write("目前處於「靜默模式」，點擊下方按鈕才會向您的 Telegram 發送報告。")
    
    if st.button("🚀 請求戰報：同步至手機 Telegram"):
        async def send_msg():
            report = (
                f"🎖️ Trinity 戰情回報\n"
                f"--------------------\n"
                f"指令：{sig}\n"
                f"價位：{data['price']:.2f}\n"
                f"量比：{data['v_ratio']:.2f}x\n"
                f"動作：{act}\n"
                f"--------------------\n"
                f"時間：{datetime.now().strftime('%H:%M')}"
            )
            bot = Bot(token=TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=report)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_msg())
            st.success("✅ 戰報已送達統帥手機！")
        except Exception as e:
            st.error(f"通訊失敗：{e}")

else:
    st.warning("⚠️ 數據連線中，請稍候或重新整理頁面...")
