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
            "bias": bias, "v_ratio": v_ratio, "v_curr": v_curr
        }
    except Exception as e:
        st.error(f"⚠️ 偵查受阻：{e}")
        return None

# ==========================================
# 🚀 執行主程序
# ==========================================

# --- 💰 側邊欄控制區 ---
st.sidebar.title("💰 戰術配置室")
capital = st.sidebar.number_input("總火種 (NTD)", value=1000000, min_value=1000, step=100000)
entry_price = st.sidebar.number_input("第一梯隊進場價 (若無則填0)", value=0.0, step=0.1)

st.title("🎖️ Trinity V3.1 雲端指揮部")
st.caption(f"偵查頻率：5 分鐘 | 現在時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

data = fetch_market_data()

if data:
    # 1. 兵力拆分換算 (50/50 分兵邏輯)
    contract_val = data['price'] * 1000
    cap_split = capital * 0.5
    pos_35x = math.floor((cap_split * 3.5) / contract_val)
    pos_60x = math.floor((cap_split * 6.0) / contract_val)
    total_pos = pos_35x + pos_60x

    # 2. 趨勢與加碼判定
    is_ma20_down = data['ma20'] < data['ma20_prev']
    is_ma20_up = data['ma20'] > data['ma20_prev']
    is_climax_16 = data['v_ratio'] > 1.6
    
    target_addon = entry_price * 1.02 if entry_price > 0 else 0
    is_addon_reached = data['price'] >= target_addon if target_addon > 0 else False

    # 3. 戰術指令判定
    sig, act, color, alert_icon = "💤 靜默", "等待指標共振", "info", ""

    # 多頭判定
    if data['price'] > data['ma20'] and data['price'] >= data['n20h']:
        if data['v_ratio'] > 1.2 and data['bias'] <= 5.5:
            sig, act, color = "🔥 FIRE 多單點火", f"第一梯隊 {pos_35x} 口已進場" if entry_price > 0 else f"建議進場第一梯隊 {pos_35x} 口", "success"
            if is_addon_reached:
                sig = "🚀 FIRE 全力進攻"
                act = f"已達加碼點 {target_addon:.2f}，投入剩餘 {pos_60x} 口 (總規模 {total_pos} 口)"
        elif data['bias'] > 5.5:
            sig, act, color = "⚠️ 乖離過熱", "禁止追多，等待回踩月線", "warning"
    
    # 空頭判定
    elif data['price'] < data['ma20'] and data['price'] < data['ma120'] and data['price'] <= data['n10l']:
        if is_climax_16:
            sig, act, color = "🚫 禁止放空", "台積電 1.6x 爆量，疑有護盤", "warning"
        elif is_ma20_down and data['v_ratio'] > 1.2:
            sig, act, color = "💣 ATTACK 空單突擊", f"建議總規模 {total_pos} 口", "error"
        elif not is_ma20_down:
            sig, act = "⏳ 等待月線下彎", "價格破位但月線斜率未轉負"

    # 同步撤退指令
    if data['price'] < data['ma20']:
        sig, act, color, alert_icon = "🛑 RETREAT 撤退", "跌破 20MA，全軍同步撤退清倉！", "error", "🚨"
    
    if is_climax_16:
        sig = "🏳️ 空單熔斷" + ("" if "RETREAT" in sig else " | 撤退")
        act += "\n【警報】台積電 1.6x 爆量，不論多空立即清倉！"
        color, alert_icon = "error", "🚨"

    # 4. 戰情儀表板佈局 (縮排嚴格校準區)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("0050 目前價", f"{data['price']:.2f}")
        if entry_price > 0:
            st.caption(f"成本: {entry_price:.2f} | 加碼點: {target_addon:.2f}")
        else:
            st.caption("尚未設定進場成本")

    with c2:
        st.metric("總建議口數", f"{total_pos}")
        st.caption(f"3.5x:{pos_35x}口 | 6x:{pos_60x}口 | 資:{capital/10000:.0f}萬")
    
    with c3:
        v_total_str = f"{data['v_curr'] / 1000:,.0f} K"
        st.metric("台積電量比", f"{data['v_ratio']:.2f}x", f"總量: {v_total_str}")
    
    with c4:
        bias_color = "red" if data['bias'] > 5.5 else ("#00FF00" if data['bias'] < -5.5 else "white")
        st.write(f"月線: {data['ma20']:.2f} ({'⤴️' if is_ma20_up else '⤵️'})")
        st.markdown(f"乖離率: <span style='color:{bias_color}; font-weight:bold;'>{data['bias']:.2f}%</span>", unsafe_content_type=True)

    st.divider()
    
    # 指令顯示
    display_sig = f"{alert_icon} {sig
