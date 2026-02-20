import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime

# ==========================================
# 🎖️ 指揮部最高配置 (請在此修改您的私人資訊)
# ==========================================
# 注意：st.set_page_config 必須位於程式碼最頂端
st.set_page_config(page_title="Trinity V3.1 指揮部", layout="wide")

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
        pwd = st.text_input("請輸入授權密碼", type="password")
        if st.button("核對身分"):
            if pwd == COMMAND_PASSWORD:
                st.session_state["password_correct"] = True
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()
            else:
                st.error("❌ 密碼錯誤，拒絕訪問。")
        return False
    return True

# ==========================================
# 📊 數據偵查引擎 (5分鐘刷新，自動調用內部偵測迴避)
# ==========================================
@st.cache_data(ttl=300)
def fetch_market_data():
    try:
        # 直接調用 yfinance，讓其內部使用 curl_cffi 處理 Yahoo 協議
        df_0050 = yf.download("0050.TW", period="9mo", interval="1d")
        df_2330 = yf.download("2330.TW", period="1mo", interval="1d")
        
        # 🛡️ 數據完整性檢查
        if df_0050.empty or df_2330.empty:
            return None
        if len(df_0050) < 21:
            return "DATA_INSUFFICIENT"

        # 核心價格計算
        close = df_0050['Close'].iloc[-1]
        ma20 = df_0050['Close'].rolling(20).mean().iloc[-1]
        ma120 = df_0050['Close'].rolling(120).mean().iloc[-1]
        n20h = df_0050['High'].rolling(20).max().shift(1).iloc[-1]
        n10l = df_0050['Low'].rolling(10).min().shift(1).iloc[-1]
        bias = ((close - ma20) / ma20) * 100

        # 台積電量能比計算 (5日均量)
        v_curr = df_2330['Volume'].iloc[-1]
        v5ma = df_2330['Volume'].rolling(5).mean().iloc[-1]
        v_ratio = v_curr / v5ma

        return {
            "price": close, "ma20": ma20, "ma120": ma120,
            "n20h": n20h, "n10l": n10l, "bias": bias,
            "v_ratio": v_ratio
        }
    except Exception as e:
        st.error(f"⚠️ 雅虎連線受阻：{e}")
        return None

# ==========================================
# ⚡ 戰術分析邏輯 (V3.1 終極校準版)
# ==========================================
def run_tactics(s):
    sig, act, color = "💤 靜默", "等待指標共振，邊走邊看", "info"
    is_climax_16 = s['v_ratio'] > 1.6

    # 1. 多頭判定 (Long)
    if s['price'] > s['ma20'] and s['price'] >= s['n20h']:
        if s['v_ratio'] > 1.2 and s['bias'] <= 5.5:
            sig, act, color = "🔥 FIRE 多單點火", "建議進場 2 口小 0050 期 (3.5x)\n若獲利 >2% 後加碼至 3 口 (6.0x)", "success"
        elif s['bias'] > 5.5:
            sig, act = "⚠️ 乖離過高", "目前位置不宜進場，等待月線回靠"

    # 2. 空頭判定 (Short) - 嚴格執行 1.6x 禁令
    elif s['price'] < s['ma20'] and s['price'] < s['ma120'] and s['price'] <= s['n10l']:
        if is_climax_16:
            sig, act, color = "🚫 禁止放空", "台積電量能 > 1.6x，疑有護盤或竭盡，禁止追空", "warning"
        elif s['v_ratio'] > 1.2:
            sig, act, color = "💣 ATTACK 空單突擊", "反手放空 2 口小 0050 期 (3.5x)", "error"

    # 3. 出場判定 (全自動過濾)
    if s['price'] < s['ma20']:
        sig, act, color = "🛑 RETREAT 多單撤退", "收盤跌破 20MA，多單全數清倉落袋", "error"
    
    if is_climax_16: # 針對空單持有者的無條件熔斷
        sig += " | 🏳️ 空單熔斷"
        act += "\n【緊急】空頭遭遇 1.6x 爆量，不論盈虧立即平倉！"

    return sig, act, color

# ==========================================
# 🌐 指揮部主程序執行
# ==========================================
if check_password():
    st.title("🎖️ Trinity V3.1 雲端指揮部")
    st.caption(f"偵查頻率：5 分鐘 | 現在時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    data = fetch_market_data()

    if data == "DATA_INSUFFICIENT":
        st.warning("⚠️ 數據量不足，暫時無法計算戰術指標。")
    elif data:
        sig, act, color = run_tactics(data)
        
        # 指標儀表板
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("0050 目前價", f"{data['price']:.2f}")
        c2.metric("2330 量能比", f"{data['v_ratio']:.2f}x")
        c3.metric("20MA 乖離", f"{data['bias']:.2f}%")
        c4.metric("20日高點位", f"{data['n20h']:.2f}")

        st.divider()

        # 戰術指令顯示
        if color == "success": st.success(f"### 指令：{sig}")
        elif color == "warning": st.warning(f"### 指令：{sig}")
        elif color == "error": st.error(f"### 指令：{sig}")
        else: st.info(f"### 指令：{sig}")
        
        st.markdown(f"**建議動作：**\n{act}")

        # 手動通知控制區 (靜默模式)
        st.divider()
        st.subheader("📢 戰訊手動傳輸")
        st.caption("點擊按鈕後，才會向您的手機 Telegram 發送完整戰報。")
        
        if st.button("🚀 請求發報：將目前數據傳送至手機"):
            async def send_tg():
                msg = (f"🎖️ Trinity 戰報回傳\n"
                       f"指令：{sig}\n"
                       f"價位：{data['price']:.2f}\n"
                       f"量比：{data['v_ratio']:.2f}x\n"
                       f"動作：{act}")
                bot = Bot(token=TOKEN)
                await bot.send_message(chat_id=CHAT_ID, text=msg)
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_tg())
                st.success("✅ 戰報已送達統帥手機！")
            except Exception as e:
                st.error(f"❌ 發送失敗：{e}")
    else:
        st.warning("📡 雅虎防線偵測中，系統將於 5 分鐘後自動嘗試重連。")
