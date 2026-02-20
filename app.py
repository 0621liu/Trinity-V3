import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime
import math

# ==========================================
# 🎖️ Trinity V8.C 3.1 最高配置
# ==========================================
st.set_page_config(page_title="Trinity V8.C 3.1 指揮部", layout="wide")

# 通訊密鑰
TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  

@st.cache_data(ttl=300)
def fetch_market_data():
    try:
        # 確保抓取足夠 120MA 計算的數據
        df_0050 = yf.download("0050.TW", period="1y", interval="1d")
        df_2330 = yf.download("2330.TW", period="1mo", interval="1d")
        if df_0050.empty or df_2330.empty: return None

        # 清洗 MultiIndex 欄位
        if isinstance(df_0050.columns, pd.MultiIndex):
            df_0050.columns = df_0050.columns.get_level_values(0)
        if isinstance(df_2330.columns, pd.MultiIndex):
            df_2330.columns = df_2330.columns.get_level_values(0)

        close_0050 = float(df_0050['Close'].iloc[-1])
        ma20 = float(df_0050['Close'].rolling(20).mean().iloc[-1])
        ma120 = float(df_0050['Close'].rolling(120).mean().iloc[-1])
        
        # 突破位判定 (不含今日)
        n20h = float(df_0050['High'].rolling(20).max().shift(1).iloc[-1])
        n10l = float(df_0050['Low'].rolling(10).min().shift(1).iloc[-1])
        
        # 乖離率計算
        bias = ((close_0050 - ma20) / ma20) * 100
        
        # 台積電量能
        v_curr = float(df_2330['Volume'].iloc[-1])
        v5ma = float(df_2330['Volume'].rolling(5).mean().iloc[-1])
        v_ratio = v_curr / v5ma

        return {
            "price": close_0050, "ma20": ma20, "ma120": ma120,
            "n20h": n20h, "n10l": n10l, "bias": bias, 
            "v_ratio": v_ratio, "v_curr": v_curr
        }
    except Exception as e:
        st.error(f"⚠️ 偵查受阻：{e}")
        return None

# ==========================================
# 🚀 執行主程序
# ==========================================

# --- 💰 側邊欄控制區 ---
st.sidebar.title("💰 戰術配置室")
capital = st.sidebar.number_input("總火種 (NTD)", value=30000, min_value=1000, step=10000)
entry_price = st.sidebar.number_input("第一梯隊進場價 (多單)", value=0.0, step=0.1)

st.title("🎖️ Trinity V8.C 3.1 雲端指揮部")
st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

data = fetch_market_data()

if data:
    # 1. 根據規格書執行「火力分配 (Leverage)」
    c_val = data['price'] * 1000  # 小0050期點值
    
    if capital < 100000:
        stage = "第一階段：100% 彈射"
        pos_primary = math.floor((capital * 6.0) / c_val)
        pos_secondary = 0
        desc_primary, desc_secondary = "6.0x (全倉)", "N/A"
    elif 100000 <= capital <= 3000000:
        stage = "第二階段：成長期"
        pos_primary = math.floor((capital * 0.5 * 3.5) / c_val)
        pos_secondary = math.floor((capital * 0.5 * 6.0) / c_val)
        desc_primary, desc_secondary = "3.5x (先遣)", "6.0x (加碼)"
    else:
        stage = "第三階段：帝國期"
        pos_primary = math.floor((capital * 0.5 * 3.5) / c_val)
        pos_secondary = math.floor((capital * 0.5 * 3.5) / c_val)
        desc_primary, desc_secondary = "3.5x (先遣)", "3.5x (加碼)"

    total_pos = pos_primary + pos_secondary
    target_addon = entry_price * 1.02 if entry_price > 0 else 0
    is_addon_reached = data['price'] >= target_addon if target_addon > 0 else False

    # 2. 規格書進場判定 (Entry Logic)
    sig, act, color, icon = "💤 待命靜默", "等待線價量共振", "info", "📡"

    # --- 多單 (Long) ---
    is_long_trend = data['price'] > data['ma20']
    is_long_break = data['price'] >= data['n20h']
    is_long_safety = data['bias'] <= 5.5
    is_long_vol = data['v_ratio'] > 1.2 and data['price'] > data['ma20']

    if is_long_trend and is_long_break and is_long_safety and is_long_vol:
        if entry_price == 0:
            sig, color, icon = "🔥 FIRE 多單點火", "success", "🏹"
            act = f"進場【第一手】：{pos_primary} 口 ({desc_primary})"
        elif is_addon_reached:
            sig, color, icon = "🚀 FIRE 全力加碼", "success", "⚔️"
            act = f"已達2%獲利位，追加【第二手】：{pos_secondary} 口 ({desc_secondary})"
        else:
            sig, color, icon = "📈 持倉待機", "success", "💎"
            act = f"多單續抱，等待加碼位 {target_addon:.2f}"

    # --- 空單 (Short) ---
    is_short_trend = data['price'] < data['ma20']
    is_short_guard = data['price'] < data['ma120']
    is_short_break = data['price'] <= data['n10l']
    is_short_vol = data['v_ratio'] > 1.2 and data['price'] < data['ma20']

    if is_short_trend and is_short_guard and is_short_break and is_short_vol:
        sig, color, icon = "💣 ATTACK 空單突擊", "error", "🌪️"
        act = f"符合空頭規格，建議火力：{total_pos} 口"

    # --- 🚨 撤退機制 (Exit Logic - 優先權最高) ---
    # 多單撤退：跌破 20MA
    if entry_price > 0 and data['price'] < data['ma20']:
        sig, act, color, icon = "🛑 RETREAT 撤退", "跌破 20MA，多單全數清倉！", "error", "🚨"
    
    # 空頭撤退：站上 20MA
    # (註：此處需使用者自行判定當前持倉方向，代碼預設警示跌破/站回)

    # 空頭特有熔斷：台積電 1.6x 爆量
    if data['v_ratio'] > 1.6:
        sig, icon = "🏳️ 熔斷 | 禁止放空", "🚨"
        act = "【爆量警報】台積電量比 > 1.6x！空單無條件出場，嚴禁進場！"
        color = "error"

    # 3. 戰情儀表板
    st.sidebar.markdown(f"**作戰階段：** {stage}")
    st.sidebar.markdown(f"**建議總量：** {total_pos} 口")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("0050 現價", f"{data['price']:.2f}")
        st.caption(f"成本: {entry_price if entry_price > 0 else '未設定'}")
    with c2:
        st.metric("20MA (月線)", f"{data['ma20']:.2f}")
        st.write(f"120MA: {data['ma120']:.2f}")
    with c3:
        v_color = "normal" if data['v_ratio'] < 1.6 else "inverse"
        st.metric("2330 量能比", f"{data['v_ratio']:.2f}x", delta=f"{'達標' if data['v_ratio']>1.2 else '未達標'}")
    with c4:
        st.metric("乖離率", f"{data['bias']:.2f}%", delta="上限 5.5%", delta_color="inverse")

    st.divider()
    
    # 指令發布區
    st.markdown(f"### {icon} 指令：{sig}")
    st.info(f"**戰術動作：** {act}")

    # 4. 手動發報功能
    if st.button("🚀 請求發報：同步至手機"):
        async def send_tg():
            msg = (f"🎖️ Trinity V8.C 3.1 戰報\n"
                   f"狀態：{sig}\n"
                   f"現價：{data['price']:.2f}\n"
                   f"量能：{data['v_ratio']:.2f}x\n"
                   f"動作：{act}\n"
                   f"備註：禁用 ATR 停損")
            bot = Bot(token=TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=msg)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_tg())
            st.success("✅ 戰報已送達統帥手機！")
        except Exception as e:
            st.error(f"發送失敗：{e}")

else:
    st.warning("📡 指揮部正與交易所建立加密連線...")
