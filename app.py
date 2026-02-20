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
# 🚀 執行主程序
# ==========================================

# --- 💰 資金調度室 (左半邊固定顯示區) ---
st.sidebar.title("💰 資金調度室")
capital = st.sidebar.number_input("總預算 (NTD)", value=1000000, step=100000)
st.sidebar.divider()
st.sidebar.write("**🎯 規格參考**")
st.sidebar.write("- 小0050：1 點 = 1,000 NTD")
st.sidebar.write("- 原始保證金：4,200 NTD")

st.title("🎖️ Trinity V3.1 雲端指揮部")
st.caption(f"偵查頻率：5 分鐘 | 現在時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

data = fetch_market_data()

if data:
    # 1. 換算邏輯
    contract_value = data['price'] * 1000
    pos_35x = math.floor((capital * 3.5) / contract_value)
    pos_60x = math.floor((capital * 6.0) / contract_value)
    
    # --- 🧮 側邊欄：新增槓桿資金換算 (首長要求) ---
    st.sidebar.divider()
    st.sidebar.subheader("📉 槓桿所需準備金/口")
    st.sidebar.write(f"以現價 **{data['price']:.2f}** 計算：")
    st.sidebar.info(f"**3.5 倍槓桿：**\n每口準備 **{contract_value / 3.5:,.0f}** NTD")
    st.sidebar.warning(f"**6.0 倍槓桿：**\n每口準備 **{contract_value / 6.0:,.0f}** NTD")
    st.sidebar.caption("※ 此金額包含保證金與緩衝資金")

    # 2. 趨勢判定
    is_ma20_down = data['ma20'] < data['ma20_prev']
    is_ma20_up = data['ma20'] > data['ma20_prev']
    is_climax_16 = data['v_ratio'] > 1.6

    # 3. 戰術分析邏輯
    sig, act, color, target_pos = "💤 靜默", "等待指標共振", "info", 0

    if data['price'] > data['ma20'] and is_ma20_up and data['price'] >= data['n20h']:
        if data['v_ratio'] > 1.2 and data['bias'] <= 5.5:
            sig, act, color = "🔥 FIRE 多單點火", f"建議建立 {pos_35x} 口，獲利 >2% 後加碼至 {pos_60x} 口", "success"
            target_pos = pos_35x
        elif data['bias'] > 5.5:
            sig, act = "⚠️ 乖離過高", "禁止追多，等待回踩月線"
    
    elif data['price'] < data['ma20'] and data['price'] < data['ma120'] and data['price'] <= data['n10l']:
        if is_climax_16:
            sig, act, color = "🚫 禁止放空", "台積電 1.6x 爆量，疑有護盤，禁止追空", "warning"
        elif is_ma20_down and data['v_ratio'] > 1.2:
            sig, act, color = "💣 ATTACK 空單突擊", f"反手建立 {pos_35x} 口空單", "error"
            target_pos = pos_35x
        elif not is_ma20_down:
            sig, act = "⏳ 等待月線下彎", "價格已破位，但月線斜率尚未轉負"

    if data['price'] < data['ma20']:
        sig, act, color = "🛑 RETREAT 撤退", "收盤跌破 20MA 全數平倉", "error"
    if is_climax_16:
        sig += " | 🏳️ 空單熔斷"
        act += "\n【警報】1.6x 爆量，空單立即平倉！"

    # 4. 戰情儀表板
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("0050 目前價", f"{data['price']:.2f}")
    c2.metric("建議口數 (3.5x/6x)", f"{pos_35x} / {pos_60x}")
    c3.metric("台積電量比", f"{data['v_ratio']:.2f}x")
    c4.metric("月線趨勢", "⤴️ 上揚" if is_ma20_up else "⤵️ 下彎")

    sc1, sc2, sc3 = st.columns(3)
    sc1.caption(f"20MA 乖離率：{data['bias']:.2f}%")
    sc2.caption(f"20日壓力位 (高點)：{data['n20h']:.2f}")
    sc3.caption(f"10日支撐位 (低點)：{data['n10l']:.2f}")

    st.divider()
    if color == "success": st.success(f"### 指令：{sig}")
    elif color == "warning": st.warning(f"### 指令：{sig}")
    elif color == "error": st.error(f"### 指令：{sig}")
    else: st.info(f"### 指令：{sig}")
    st.write(f"**建議戰術：** {act}")

    # 5. 手動發報
    if st.button("🚀 請求發報：同步至手機"):
        async def send_tg():
            msg = (f"🎖️ Trinity 戰報\n指令：{sig}\n現價：{data['price']:.2f}\n建議口數：{target_pos} 口\n動作：{act}")
            bot = Bot(token=TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=msg)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_tg())
            st.success("✅ 戰報已送達！")
        except Exception as e:
            st.error(f"發送失敗：{e}")
else:
    st.warning("📡 偵查雷達重啟中，請稍候...")
