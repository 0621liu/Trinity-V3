import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- APP 設定 (雲端優化版) ---
st.set_page_config(page_title="Trinity V3.1 終極指揮部", layout="wide")
st.title("🎖️ Trinity V3.1 雲端指揮部")

# --- 側邊欄：資產情報 ---
st.sidebar.header("💰 資產情報")
capital = st.sidebar.number_input("當前帳戶總資產 (TWD)", value=30000, step=1000)

# 自動判定戰略模式
if capital < 100000:
    strategy, leverage = "🔥 火種點火 (Ignition)", 6.0
elif capital < 3000000:
    strategy, leverage = "🛡️ 方陣分兵 (Phalanx)", 4.75
else:
    strategy, leverage = "🏰 堡壘防禦 (Fortress)", 3.5

st.sidebar.info(f"**戰略模式：**\n{strategy}")
st.sidebar.write(f"系統建議總槓桿：**{leverage}x**")

# --- 數據抓取函數 (增加強韌性) ---
@st.cache_data(ttl=600)
def get_data():
    try:
        # 下載 0050 與 2330
        d050 = yf.download("0050.TW", period="6mo", progress=False)
        d2330 = yf.download("2330.TW", period="1mo", progress=False)
        
        # 強制清理 MultiIndex (yfinance v0.2.40+ 必備)
        if isinstance(d050.columns, pd.MultiIndex):
            d050.columns = d050.columns.get_level_values(0)
        if isinstance(d2330.columns, pd.MultiIndex):
            d2330.columns = d2330.columns.get_level_values(0)
            
        # 提取最新純數值
        curr_p = float(d050['Close'].iloc[-1])
        ma20 = float(d050['Close'].rolling(20).mean().iloc[-1])
        n20h = float(d050['High'].rolling(20).max().shift(1).iloc[-1])
        
        v5ma_tsmc = float(d2330['Volume'].tail(5).mean())
        curr_v_tsmc = float(d2330['Volume'].iloc[-1])
        vol_ratio = curr_v_tsmc / v5ma_tsmc if v5ma_tsmc > 0 else 0
        
        bias = ((curr_p - ma20) / ma20) * 100
        
        return curr_p, ma20, n20h, vol_ratio, bias
    except Exception as e:
        st.error(f"數據抓取失敗：{str(e)}")
        return None

# --- 渲染介面 ---
data = get_data()

if data:
    p, m20, nh, v_ratio, b = data
    
    st.header(f"📊 即時戰況偵測 (0050: {p:.2f})")
    c1, c2, c3 = st.columns(3)
    c1.metric("價格位階", f"{p:.2f}", f"{p-m20:.2f}")
    c2.metric("台積電動能", f"{v_ratio:.2f}x", "目標 1.20x")
    c3.metric("乖離率", f"{b:.1f}%", "上限 5.5%")

    # 燈號邏輯
    is_trend = p > m20 and p >= nh
    is_vol = v_ratio >= 1.2
    is_safe = b <= 5.5

    st.markdown("---")
    if is_trend and is_vol and is_safe:
        st.success("🔥 [FIRE] 指標全亮，符合 V3.1 進場訊號！")
    elif p < m20:
        st.error("🛑 [RETREAT] 價格低於月線，維持撤退狀態。")
    else:
        st.warning("💤 [WAIT] 指標未全亮，狙擊手保持靜默。")

    # 彈藥試算
    st.subheader(f"⚔️ {strategy} - 彈藥分配建議")
    exposure = capital * leverage
    lots = exposure / (p * 1000)
    
    res1, res2, res3 = st.columns(3)
    res1.write(f"總曝險額: **{exposure:,.0f}**")
    res2.write(f"建議口數: **{round(lots, 1)} 口**")
    res3.write(f"更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
