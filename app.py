import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 介面設定 (完全鎖定：無多餘標題) ---
st.set_page_config(page_title="Trinity V3.1 雲端指揮部", layout="wide")
st.title("🎖️ Trinity V8.C 3.1 戰略終端")

# --- 2. 左側側邊欄 (還原：僅存參數配置) ---
st.sidebar.header("⚙️ 戰術參數配置")
init_cap = st.sidebar.number_input("起始本金", value=30000)
monthly_add = st.sidebar.number_input("每月補給", value=10000)

st.sidebar.markdown("---")
st.sidebar.warning("⚡ 戰術核心：線、價、量。")

# --- 3. 數據核心 ---
@st.cache_data(ttl=3600)
def get_battle_data():
    start_d, end_d = "2019-06-01", datetime.now().strftime('%Y-%m-%d')
    s50 = yf.download("0050.TW", start=start_d, end=end_d, auto_adjust=True)
    s2330 = yf.download("2330.TW", start=start_d, end=end_d, auto_adjust=True)
    for s in [s50, s2330]:
        if isinstance(s.columns, pd.MultiIndex): s.columns = s.columns.get_level_values(0)
    df = pd.DataFrame(index=s50.index)
    df['C'], df['H'], df['L'] = s50['Close'], s50['High'], s50['Low']
    df['V_2330'] = s2330['Volume']
    df['20MA'] = df['C'].rolling(20).mean()
    df['120MA'] = df['C'].rolling(120).mean()
    df['N20_H'] = df['H'].shift(1).rolling(20).max()
    df['N10_L'] = df['L'].shift(1).rolling(10).min()
    df['V5MA'] = df['V_2330'].rolling(5).mean()
    df['Bias'] = (df['C'] - df['20MA']) / df['20MA']
    return df.dropna()

df = get_battle_data()

# --- 4. 戰場模擬 (還原：純淨運算，不留紀錄表) ---
def run_simulation(df, capital, monthly_add):
    cap = float(capital)
    tai_zuo_fund = 0.0
    withdrawn = False
    pos, entry_p, add_p = 0, 0.0, 0.0
    last_m, is_full = -1, False
    trade_count = 0

    for date, row in df.loc['2020-01-01':].iterrows():
        if date.month != last_m:
            cap += monthly_add; last_m = date.month
        if cap >= 1000000 and not withdrawn:
            tai_zuo_fund = 30000 + (trade_count * 10000)
            cap -= tai_zuo_fund; withdrawn = True

        p, ma20, v_ratio = row['C'], row['20MA'], row['V_2330'] / row['V5MA']
        wealth = cap + tai_zuo_fund

        if pos != 0:
            if not is_full:
                move = (p - entry_p)/entry_p if pos == 1 else (entry_p - p)/entry_p
                if move >= 0.02: is_full = True; add_p = p
            exit_f = False
            if pos == 1 and p < ma20: exit_f = True
            if pos == -1 and (v_ratio > 1.6 or p > ma20): exit_f = True
            if exit_f:
                if wealth < 100000: roi = (p - entry_p) / entry_p * 6.0 * pos
                else:
                    l1, l2 = (3.5, 6.0) if wealth < 3000000 else (3.5, 3.5)
                    r1 = (p - entry_p) / entry_p * l1 * 0.5 * pos
                    r2 = (p - add_p) / add_p * l2 * 0.5 * pos if (is_full and add_p > 0) else 0
                    roi = r1 + r2
                cap *= (1 + roi); trade_count += 1
                pos, is_full, add_p = 0, False, 0.0

        if pos == 0:
            vol_f = v_ratio > 1.2
            if p > ma20 and p >= row['N20_H'] and vol_f and row['Bias'] <= 0.055:
                pos, entry_p, is_full, add_p = 1, p, (wealth < 100000), p
            elif p < ma20 and p < row['120MA'] and p <= row['N10_L'] and vol_f and v_ratio <= 1.6 and row['Bias'] >= -0.055:
                pos, entry_p, is_full, add_p = -1, p, (wealth < 100000), p
    return cap, tai_zuo_fund

final_cap, final_wife = run_simulation(df, init_cap, monthly_add)

# --- 5. 右側主介面 (還原：純淨資產看板) ---
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("⚔️ 戰鬥餘額", f"${int(final_cap):,}")
c2.metric("🏠 安太座金庫", f"${int(final_wife):,}")
c3.metric("📈 總資產規模", f"${int(final_cap + final_wife):,}")

# --- 6. 13:25 即時判定區 (還原：點火雷達) ---
st.divider()
st.subheader("🚀 13:25 點火雷達")
last_row = df.iloc[-1]
v_r = last_row['V_2330'] / last_row['V5MA']
col1, col2, col3, col4 = st.columns(4)
col1.write(f"現價: **{last_row['C']:.2f}**")
col2.write(f"月線: **{last_row['20MA']:.2f}**")
col3.write(f"量比: **{v_r:.2f}x**")
col4.write(f"乖離: **{last_row['Bias']*100:.1f}%**")

if last_row['C'] > last_row['20MA'] and last_row['C'] >= last_row['N20_H'] and v_r > 1.2 and last_row['Bias'] <= 0.055:
    st.success("✅ 多頭訊號確立！")
elif last_row['C'] < last_row['20MA'] and last_row['C'] < last_row['120MA'] and v_r > 1.2 and last_row['Bias'] >= -0.055:
    st.error("🚨 空頭襲擊訊號！")
else:
    st.info("😴 目前無訊號。")
