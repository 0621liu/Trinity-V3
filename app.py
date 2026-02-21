import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime
import math

# ==========================================
# 🎖️ 指揮部最高配置 - 規格書 3.1 聖經執行版
# ==========================================
st.set_page_config(page_title="Trinity V3.1 指揮部", layout="wide")

TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  

@st.cache_data(ttl=300)
def fetch_market_data():
    try:
        df_0050 = yf.download("0050.TW", period="1y", interval="1d")
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
        v_price = float(df_2330['Close'].iloc[-1])
        v5ma = float(df_2330['Volume'].rolling(5).mean().iloc[-1])
        v_ratio = v_curr / v5ma

        return {
            "price": close, "ma20": ma20, "ma20_prev": ma20_prev,
            "ma120": ma120, "n20h": n20h, "n10l": n10l,
            "bias": bias, "v_ratio": v_ratio, "v_curr": v_curr, "v_price": v_price
        }
    except Exception as e:
        st.error(f"⚠️ 偵查受阻：{e}")
        return None

# ==========================================
# 🚀 執行主程序 - 左側配置室 (UI 嚴格鎖定)
# ==========================================

st.sidebar.title("💰 戰術配置室")
capital = st.sidebar.number_input("總火種 (NTD)", value=30000, min_value=1000, step=10000)
entry_price_input = st.sidebar.number_input("第一梯隊進場價", value=0.0, step=0.1)
pos_direction = st.sidebar.selectbox("當前持倉方向", ["無", "多單", "空單"])

data = fetch_market_data()

if data:
    contract_value = data['price'] * 1000
    m_35x = contract_value / 3.5
    m_60x = contract_value / 6.0

    # --- 核心邏輯修改：分兵與比例 (不變動變數名稱，僅改動數值計算) ---
    if capital < 100000:
        pos_35x = math.floor(capital / m_60x) # 第一階段 6.0x 彈射
        pos_60x = 0
        used_margin = pos_35x * m_60x
        tier1_label = "第一階段彈射 (6.0x)"
    elif capital <= 3000000:
        # 第二階段：20% (3.5x) / 80% (6.0x)
        pos_35x = math.floor((capital * 0.2) / m_35x)
        pos_60x = math.floor((capital * 0.8) / m_60x)
        used_margin = pos_35x * m_35x
        tier1_label = "第一手先遣 (20%)"
    else:
        # 第三階段：30% (3.5x) / 70% (6.0x)
        pos_35x = math.floor((capital * 0.3) / m_35x)
        pos_60x = math.floor((capital * 0.7) / m_60x)
        used_margin = pos_35x * m_35x
        tier1_label = "第一手先遣 (30%)"
    
    total_pos = pos_35x + pos_60x
    remaining_margin = capital - used_margin

    # 保持側欄 Markdown 視覺排版不變
    st.sidebar.markdown(f"""
    <div style="background-color:#111111; padding:15px; border-radius:10px; border:2px solid #444; margin-top:10px;">
        <p style="color:#E0E0E0; font-size:13px; margin-bottom:2px; font-weight:500;">{tier1_label} 佔用資本</p>
        <p style="color:#FFFFFF; font-size:20px; font-weight:bold; margin-bottom:12px;">{used_margin:,.0f} 元</p>
        <p style="color:#E0E0E0; font-size:13px; margin-bottom:2px; font-weight:500;">🟢 剩餘保證金 (預留主力部隊)</p>
        <p style="color:#00FF00; font-size:26px; font-weight:bold;">{remaining_margin:,.0f} 元</p>
        <hr style="border:0.5px solid #555; margin:12px 0;">
        <p style="color:#BBBBBB; font-size:11px;">每口 3.5x 基準：{m_35x:,.0f}</p>
        <p style="color:#BBBBBB; font-size:11px;">每口 6.0x 基準：{m_60x:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 📈 右側主畫面 (絕對鎖定，禁止改動)
# ==========================================
st.title("🎖️ Trinity V3.1 雲端指揮部")
st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if data:
    is_ma20_up = data['ma20'] > data['ma20_prev']
    is_climax_16 = data['v_ratio'] > 1.6
    
    # 校準加碼邏輯
    if entry_price_input > 0:
        if pos_direction == "多單":
            target_addon = entry_price_input * 1.02
            is_addon_reached = data['price'] >= target_addon
        elif pos_direction == "空單":
            target_addon = entry_price_input * 0.98
            is_addon_reached = data['price'] <= target_addon
        else:
            target_addon, is_addon_reached = 0, False
    else:
        target_addon, is_addon_reached = 0, False

    sig, act, color, icon = "💤 靜默", "等待指標共振", "info", ""
    
    # 邏輯判定 (多頭)
    if data['price'] > data['ma20'] and data['price'] >= data['n20h']:
        if data['v_ratio'] > 1.2 and data['bias'] <= 5.5:
            sig, color = "🔥 FIRE 多單點火", "success"
            act = f"進場先遣部隊 {pos_35x} 口" if entry_price_input == 0 else "先遣已持倉，等待加碼位"
            if is_addon_reached:
                sig, act = "🚀 FIRE 全力進攻", f"已達 2% 加碼位 {target_addon:.2f}，投入主力 {pos_60x} 口 (6.0x)"
        elif data['bias'] > 5.5:
            sig, act, color = "⚠️ 乖離過熱", "禁止追多，等待回踩月線", "warning"
            
    # 邏輯判定 (空頭 - 修改重點：-6% 乖離鎖)
    elif data['price'] < data['ma20'] and data['price'] < data['ma120'] and data['price'] <= data['n10l']:
        if is_climax_16:
            sig, act, color = "🚫 禁止放空", "台積電 1.6x 爆量護盤 (熔斷禁區)", "warning"
        elif data['bias'] < -6.0: # 修正為 -6% 禁入
            sig, act, color = "⚠️ 乖離過大", "低於 -6% 禁區，禁止追空", "warning"
        elif data['v_ratio'] > 1.2:
            sig, act, color = "💣 ATTACK 空單突擊", f"建立空單先遣，投入 {pos_35x} 口", "error"
            if is_addon_reached:
                sig, act = "🚀 ATTACK 全力重擊", f"已達 2% 跌幅加碼位 {target_addon:.2f}，投入主力 {pos_60x} 口 (6.0x)"

    # 出場判定 (多單/空單 通用 20MA)
    if (pos_direction == "多單" and data['price'] < data['ma20']) or (pos_direction == "空單" and data['price'] > data['ma20']):
        sig, act, color, icon = "🛑 RETREAT 撤退", "觸碰 20MA，全軍清倉撤退！", "error", "🚨🚨🚨"
    
    # 出場判定 (空單 1.6x 熔斷)
    if pos_direction == "空單" and is_climax_16:
        sig, icon, color = "🏳️ 空單熔斷 | 全軍撤退", "🚨🚨🚨", "error"
        act = "【緊急】台積電 1.6x 爆量，空單無條件清倉！"

    # UI 顯示部分 (結構絕對鎖定)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("0050 目前價", f"{data['price']:.2f}")
        if entry_price_input > 0:
            st.markdown(f"<p style='color:black; font-size:18px; font-weight:bold;'>成本: {entry_price_input:.2f} | 加碼: {target_addon:.2f}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#555; font-size:16px;'>成本: 未設定</p>", unsafe_allow_html=True)
    with c2:
        st.metric("建議總口數", f"{total_pos} 口")
        st.markdown(f"<p style='color:black; font-size:16px; font-weight:bold;'>先遣: {pos_35x}口 | 主力: {pos_60x}口</p>", unsafe_allow_html=True)
    with c3:
        v_total = f"{data['v_curr'] / 1000:,.0f} K"
        st.metric("台積電量比", f"{data['v_ratio']:.2f}x", f"總量: {v_total}")
        st.markdown(f"<p style='color:black; font-size:16px; font-weight:bold;'>2330股價: {data['v_price']:.1f}</p>", unsafe_allow_html=True)
    with c4:
        # 乖離燈號顏色邏輯同步 -6%
        b_clr = "red" if data['bias'] > 5.5 else ("#00FF00" if data['bias'] < -6.0 else "white")
        st.write(f"月線: {data['ma20']:.2f} ({'⤴️' if is_ma20_up else '⤵️'})")
        st.markdown(f"乖離率: <span style='color:{b_clr}; font-weight:bold; font-size:20px;'>{data['bias']:.2f}%</span>", unsafe_allow_html=True)

    st.divider()
    d_sig = f"{icon} {sig} {icon}" if icon else sig
    if color == "success": st.success(f"### 指令：{d_sig}")
    elif color == "warning": st.warning(f"### 指令：{d_sig}")
    elif color == "error": st.error(f"### 指令：{d_sig}")
    else: st.info(f"### 指令：{d_sig}")
    st.write(f"**建議動作：**\n{act}")

    if st.button("🚀 請求發報：同步至手機"):
        st.info("Telegram 功能已依照首長指示暫時轉為手動觀察模式。")
else:
    st.warning("📡 偵查雷達重啟中...")
