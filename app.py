import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime

# ==========================================
# 🎖️ 指揮部最高配置
# ==========================================
st.set_page_config(page_title="Trinity V3.1 指揮部", layout="wide")

TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  
COMMAND_PASSWORD = "2836" 

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🎖️ Trinity 系統：身份驗證")
        pwd = st.text_input("請輸入授權密碼", type="password")
        if st.button("登入系統"):
            if pwd == COMMAND_PASSWORD:
                st.session_state["password_correct"] = True
                if hasattr(st, "rerun"): st.rerun()
                else: st.experimental_rerun()
            else:
                st.error("❌ 密碼錯誤")
        return False
    return True

# ==========================================
# 📊 數據偵查引擎 (加入月線斜率判定)
# ==========================================
@st.cache_data(ttl=300)
def fetch_market_data():
    try:
        df_0050 = yf.download("0050.TW", period="9mo", interval="1d")
        df_2330 = yf.download("2330.TW", period="1mo", interval="1d")
        
        if df_0050.empty or df_2330.empty: return None

        if isinstance(df_0050.columns, pd.MultiIndex):
            df_0050.columns = df_0050.columns.get_level_values(0)
        if isinstance(df_2330.columns, pd.MultiIndex):
            df_2330.columns = df_2330.columns.get_level_values(0)

        # 核心指標提取
        close = float(df_0050['Close'].iloc[-1])
        ma20_series = df_0050['Close'].rolling(20).mean()
        ma20 = float(ma20_series.iloc[-1])
        ma20_prev = float(ma20_series.iloc[-2]) # 👈 取得昨日月線
        
        ma120 = float(df_0050['Close'].rolling(120).mean().iloc[-1])
        n20h = float(df_0050['High'].rolling(20).max().shift(1).iloc[-1])
        n10l = float(df_0050['Low'].rolling(10).min().shift(1).iloc[-1])
        
        bias = ((close - ma20) / ma20) * 100
        
        # 趨勢判定
        is_ma20_down = ma20 < ma20_prev # 👈 月線下彎
        is_ma20_up = ma20 > ma20_prev   # 👈 月線上揚
        
        # 台積電量能比
        v_curr = float(df_2330['Volume'].iloc[-1])
        v5ma = float(df_2330['Volume'].rolling(5).mean().iloc[-1])
        v_ratio = v_curr / v5ma

        return {
            "price": close, "ma20": ma20, "ma120": ma120,
            "n20h": n20h, "n10l": n10l, "bias": bias,
            "v_ratio": v_ratio, "is_ma20_down": is_ma20_down,
            "is_ma20_up": is_ma20_up
        }
    except Exception as e:
        st.error(f"⚠️ 偵查受阻：{e}")
        return None

# ==========================================
# ⚡ 戰術分析模組 (加入月線斜率濾網)
# ==========================================
def run_tactics(s):
    sig, act, color = "💤 靜默", "等待指標共振", "info"
    is_climax_16 = s['v_ratio'] > 1.6

    # 1. 多頭判定 (Long)
    # 增加：必須月線上揚
    if s['price'] > s['ma20'] and s['is_ma20_up'] and s['price'] >= s['n20h']:
        if s['v_ratio'] > 1.2 and s['bias'] <= 5.5:
            sig, act, color = "🔥 FIRE 多單點火", "進場 2 口小 0050 期 (3.5x)", "success"
        elif s['bias'] > 5.5:
            sig, act = "⚠️ 乖離過高", "禁止追多，等待回踩月線"

    # 2. 空頭判定 (Short)
    # 增加：必須月線下彎
    elif s['price'] < s['ma20'] and s['price'] < s['ma120'] and s['price'] <= s['n10l']:
        if is_climax_16:
            sig, act, color = "🚫 禁止放空", "1.6x 爆量避險，禁止追空", "warning"
        elif s['is_ma20_down'] and s['v_ratio'] > 1.2: # 👈 關鍵濾網：月線需下彎
            sig, act, color = "💣 ATTACK 空單突擊", "反手放空 2 口小 0050 期 (3.5x)", "error"
        elif not s['is_ma20_down']:
            sig, act = "⏳ 等待月線下彎", "價位已跌破，但月線尚未轉向，暫不進場"

    # 3. 出場判定
    if s['price'] < s['ma20']:
        sig, act, color = "🛑 RETREAT 撤退", "跌破 20MA 全數平倉", "error"
    if is_climax_16:
        sig += " | 🏳️ 空單熔斷"
        act += "\n【警報】空單遇 1.6x 爆量立即平倉！"

    return sig, act, color

# ==========================================
# 🚀 執行主程序
# ==========================================
if check_password():
    st.title("🎖️ Trinity V3.1 雲端指揮部")
    st.caption(f"偵查頻率：5 分鐘 | 現在時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    data = fetch_market_data()

    if data:
        sig, act, color = run_tactics(data)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("0050 目前價", f"{data['price']:.2f}")
        c2.metric("2330 量能比", f"{data['v_ratio']:.2f}x")
        c3.metric("月線趨勢", "⤴️ 上揚" if data['is_ma20_up'] else "⤵️ 下彎")
        c4.metric("20MA 乖離", f"{data['bias']:.1f}%")

        st.divider()
        if color == "success": st.success(f"### 指令：{sig}")
        elif color == "warning": st.warning(f"### 指令：{sig}")
        elif color == "error": st.error(f"### 指令：{sig}")
        else: st.info(f"### 指令：{sig}")
        st.write(f"**建議戰術：** {act}")

        # 手動通知
        if st.button("🚀 請求發報"):
            async def send_tg():
                trend_str = "上揚" if data['is_ma20_up'] else "下彎"
                msg = f"🎖️ Trinity 戰報\n指令：{sig}\n價位：{data['price']:.2f}\n月線趨勢：{trend_str}\n動作：{act}"
                bot = Bot(token=TOKEN)
                await bot.send_message(chat_id=CHAT_ID, text=msg)
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_tg())
                st.success("✅ 戰報已送達！")
            except Exception as e:
                st.error(f"發送失敗：{e}")

