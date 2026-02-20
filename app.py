import streamlit as st
import yfinance as yf
import pandas as pd

# --- APP 設定 ---
st.set_page_config(page_title="Trinity V3.1 強韌版", layout="wide")
st.title("🎖️ Trinity V3.1 股期指揮部 [V3.11 強韌版]")

# --- 側邊欄：資產情報 ---
st.sidebar.header("💰 資產情報")
capital = st.sidebar.number_input("當前帳戶總資產 (TWD)", value=30000, step=1000)

if capital < 100000:
    strategy_mode, target_leverage = "🔥 火種點火 (Ignition)", 6.0
elif capital < 3000000:
    strategy_mode, target_leverage = "🛡️ 方陣分兵 (Phalanx)", 4.75
else:
    strategy_mode, target_leverage = "🏰 堡壘防禦 (Fortress)", 3.5

st.sidebar.info(f"**戰略模式：**\n{strategy_mode}")
st.sidebar.write(f"系統建議總槓桿：**{target_leverage}x**")

# --- 核心數據抓取 (強化版：強制降維處理) ---
@st.cache_data(ttl=3600)
def get_market_metrics():
    # 抓取數據並強制處理 MultiIndex
    d050 = yf.download("0050.TW", period="6mo", progress=False)
    d2330 = yf.download("2330.TW", period="1mo", progress=False)
    
    # 如果 yfinance 回傳多重索引，只取第一層
    if isinstance(d050.columns, pd.MultiIndex):
        d050.columns = d050.columns.get_level_values(0)
    if isinstance(d2330.columns, pd.MultiIndex):
        d2330.columns = d2330.columns.get_level_values(0)

    # 精確選取最後一個純數值 (float)
    curr_price = float(d050['Close'].iloc[-1])
    ma20 = float(d050['Close'].rolling(20).mean().iloc[-1])
    n20_h = float(d050['High'].rolling(20).max().shift(1).iloc[-1])
    
    v5ma_2330 = float(d2330['Volume'].tail(5).mean())
    curr_v_2330 = float(d2330['Volume'].iloc[-1])
    vol_ratio = curr_v_2330 / v5ma_2330
    
    bias = ((curr_price - ma20) / ma20) * 100
    
    return curr_price, ma20, n20_h, vol_ratio, bias

# 執行與渲染
try:
    p, m20, nh, v_ratio, b = get_market_metrics()

    # --- 戰場看板 ---
    st.header(f"📊 即時戰況偵測 (0050: {p:.2f})")
    col1, col2, col3 = st.columns(3)
    col1.metric("價格位階", f"{p:.2f}", f"{p-m20:.2f} (vs 月線)")
    col2.metric("台積電動能", f"{v_ratio:.2f}x", "門檻 1.20x")
    col3.metric("乖離防線", f"{b:.1f}%", "上限 5.5%")

    # --- 燈號 ---
    is_trend, is_vol, is_safe = (p > m20 and p >= nh), (v_ratio >= 1.2), (b <= 5.5)

    if is_trend and is_vol and is_safe:
        st.success("🔥 [FIRE] 訊號全亮！符合 V3.1 點火條件。")
    elif p < m20:
        st.error("🛑 [RETREAT] 跌破月線，全軍撤退。")
    else:
        st.warning("💤 [WAIT] 條件未成熟，狙擊手保持靜默。")

    # --- 彈藥計算 ---
    st.subheader(f"⚔️ {strategy_mode} - 彈藥建議")
    total_exposure = capital * target_leverage
    suggested_lots = total_exposure / (p * 1000)

    r1, r2, r3 = st.columns(3)
    r1.write(f"當前總資產: **{capital:,.0f}**")
    r2.write(f"目標曝險額: **{total_exposure:,.0f}**")
    r3.write(f"建議口數: **{round(suggested_lots, 1)} 口**")

except Exception as e:
    st.error(f"📡 戰場雷達干擾中: {str(e)}")