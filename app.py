import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime
import math

# ==========================================
# 🎖️ 指揮部最高配置 - 嚴格執行規格書 3.1 邏輯
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
# 🚀 執行主程序
# ==========================================

# --- 💰 左側側邊欄 (槓桿保證金換算版) ---
st.sidebar.title("💰 戰術配置室")
capital = st.sidebar.number_input("總火種 (NTD)", value=30000, min_value=1000, step=10000)
entry_price_input = st.sidebar.number_input("第一梯隊進場價", value=0.0, step=0.1)

data = fetch_market_data()

if data:
    # 1. 戰術階段與基準保證金計算
    contract_value = data['price'] * 1000
    m_35x = contract_value / 3.5  # 3.5倍實質保證金
    m_60x = contract_value / 6.0  # 6.0倍實質保證金

    # 2. 兵力拆分邏輯
    if capital < 100000:
        # 第一階段：100% 資金跑 6.0x
        pos_35x = math.floor(capital / m_60x) 
        pos_60x = 0
        used_margin = pos_35x * m_60x
        tier1_label = "第一梯隊 (6.0x)"
    else:
        # 第二、三階段：50% 資金跑對應槓桿
        cap_split = capital * 0.5
        pos_35x = math.floor(cap_split / m_35x)
        if capital <= 3000000:
            pos_60x = math.floor(cap_split / m_60x)
        else:
            pos_60x = math.floor(cap_split / m_35x)
        used_margin = pos_35x * m_35x
        tier1_label = "第一梯隊 (3.5x)"
    
    total_pos = pos_35x + pos_60x
    remaining_margin = capital - used_margin

    # 3. 左側動態顯示 (100% 符合首長需求)
    st.sidebar.markdown(f"""
    <div style="background-color:#1e1e1e; padding:12px; border-radius:8px; border:1px solid #333; margin-top:10px;">
        <p style="color:#888; font-size:12px; margin-bottom:2px;">{tier1_label} 佔用資本</p>
        <p style="color:#fff; font-size:18px; font-weight:bold; margin-bottom:12px;">{used_margin:,.0f} 元</p>
        <p style="color:#888; font-size:12px; margin-bottom:2px;">🟢 剩餘保證金 (可用資本)</p>
        <p style="color:#00FF00; font-size:24px; font-weight:bold;">{remaining_margin:,.0f} 元</p>
        <hr style="border:0.5px solid #333; margin:10px 0;">
        <p style="color:#555; font-size:11px;">每口 3.5x 基準：{m_35x:,.0f}</p>
        <p style="color:#555; font-size:11px;">每口 6.0x 基準：{m_60x:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 📈 右側主畫面 (嚴格鎖定，禁止改動)
# ==========================================
st.title("🎖️ Trinity V3.1 雲端指揮部")
st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if data:
    # 判定邏輯
    is_ma20_up = data['ma20'] > data['ma20_prev']
    is_climax_16 = data['v_ratio'] > 1.6
    target_addon = entry_price_input * 1.02 if entry_price_input > 0 else 0
    is_addon_reached = data['price'] >= target_addon if target_addon > 0 else False

    # 戰術指令
    sig, act, color, icon = "💤 靜默", "等待指標共振", "info", ""
    if data['price'] > data['ma20'] and data['price'] >= data['n20h']:
        if data['v_ratio'] > 1.2 and data['bias'] <= 5.5:
            sig, color = "🔥 FIRE 多單點火", "success"
            act = f"進場第一梯隊 {pos_35x} 口" if entry_price_input == 0 else "第一梯隊已進場，等待加碼位"
            if is_addon_reached:
                sig, act = "🚀 FIRE 全力進攻", f"已達 2% 加碼位 {target_addon:.2f}，投入剩餘 {pos_60x} 口"
        elif data['bias'] > 5.5:
            sig, act, color = "⚠️ 乖離過熱", "禁止追多，等待回踩月線", "warning"
    elif data['price'] < data['ma20'] and data['price'] < data['ma120'] and data['price'] <= data['n10l']:
        if is_climax_16:
            sig, act, color = "🚫 禁止放空", "台積電 1.6x 爆量護盤", "warning"
        elif data['v_ratio'] > 1.2:
            sig, act, color = "💣 ATTACK 空單突擊", f"反手建立空單 ({pos_35x}+{pos_60x})", "error"

    if data['price'] < data['ma20']:
        sig, act, color, icon = "🛑 RETREAT 撤退", "跌破 20MA，不論盈虧全軍撤退！", "error", "🚨🚨🚨"
    if is_climax_16:
        sig, icon, color = "🏳️ 空單熔斷 | 全軍撤退", "🚨🚨🚨", "error"
        act = "【爆量警報】台積電 1.6x 爆量，立即出清所有倉位！"

    # 4. 戰情儀表板
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("0050 目前價", f"{data['price']:.2f}")
        if entry_price_input > 0:
            st.markdown(f"<p style='color:black; font-size:18px; font-weight:bold;'>成本: {entry_price_input:.2f} | 加碼: {target_addon:.2f}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#555; font-size:16px;'>成本: 未設定</p>", unsafe_allow_html=True)
    with c2:
        st.metric("建議總口數", f"{total_pos} 口")
        st.markdown(f"<p style='color:black; font-size:16px; font-weight:bold;'>3.5x: {pos_35x}口 | 6x: {pos_60x}口</p>", unsafe_allow_html=True)
    with c3:
        v_total = f"{data['v_curr'] / 1000:,.0f} K"
        st.metric("台積電量比", f"{data['v_ratio']:.2f}x", f"總量: {v_total}")
        st.markdown(f"<p style='color:black; font-size:16px; font-weight:bold;'>2330股價: {data['v_price']:.1f}</p>", unsafe_allow_html=True)
    with c4:
        b_clr = "red" if data['bias'] > 5.5 else ("#00FF00" if data['bias'] < -5.5 else "white")
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
        async def send_tg():
            msg = f"🎖️ Trinity 戰報\n指令：{sig}\n現價：{data['price']:.2f}\n成本：{entry_price_input:.2f}\n剩餘資本：{remaining_margin:,.0f}"
            bot = Bot(token=TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=msg)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_tg())
        st.success("✅ 戰報已送達！")
else:
    st.warning("📡 偵查雷達重啟中...")
