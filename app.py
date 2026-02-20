import streamlit as st
import yfinance as yf
import pandas as pd

# --- 強制環境設定 ---
st.set_page_config(page_title="Trinity V3.1 絕對指揮部", layout="wide")

# --- 核心邏輯：穩健抓取數據 ---
@st.cache_data(ttl=600)
def fetch_market_data():
    try:
        # 下載數據 (使用 auto_adjust 確保結構穩定)
        d050 = yf.download("0050.TW", period="6mo", auto_adjust=True, progress=False)
        d2330 = yf.download("2330.TW", period="1mo", auto_adjust=True, progress=False)
        
        # 處理 MultiIndex 異常 (雲端環境常見問題)
        if isinstance(d050.columns, pd.MultiIndex):
            d050.columns = d050.columns.get_level_values(0)
        if isinstance(d2330.columns, pd.MultiIndex):
            d2330.columns = d2330.columns.get_level_values(0)
            
        # 提取最新數據
        p = float(d050['Close'].iloc[-1])
        m20 = float(d050['Close'].rolling(20).mean().iloc[-1])
        nh = float(d050['High'].rolling(20).max().shift(1).iloc[-1])
        
        v5ma = float(d2330['Volume'].tail(5).mean())
        curr_v = float(d2330['Volume'].iloc[-1])
        vr = curr_v / v5ma if v5ma > 0 else 0
        
        bias = ((p - m20) / m20) * 100
        
        return {"p": p, "m20": m20, "nh": nh, "vr": vr, "bias": bias}
    except Exception as e:
        return str(e)

# --- 渲染介面 ---
st.title("🎖️ Trinity V3.1 雲端指揮部 [絕對防禦版]")

# 側邊欄資產輸入
capital = st.sidebar.number_input("當前總資產 (TWD)", value=30000, step=1000)

res = fetch_market_data()

if isinstance(res, dict):
    # 戰場數據看板
    c1, c2, c3 = st.columns(3)
    c1.metric("0050 現價", f"{res['p']:.2f}", f"{res['p']-res['m20']:.2f} (vs 月線)")
    c2.metric("2330 量能比", f"{res['vr']:.2f}x", "門檻 1.20x")
    c3.metric("乖離率", f"{res['bias']:.1f}%", "上限 5.5%")

    # 燈號邏輯
    is_trend = res['p'] > res['m20'] and res['p'] >= res['nh']
    is_vol = res['vr'] >= 1.2
    is_safe = res['bias'] <= 5.5

    st.markdown("---")
    if is_trend and is_vol and is_safe:
        st.success("🔥 [FIRE] 訊號全亮！符合點火條件。")
    elif res['p'] < res['m20']:
        st.error("🛑 [RETREAT] 價格破月線，全軍撤退。")
    else:
        st.warning("💤 [WAIT] 指標未成熟，狙擊手靜默。")

    # 槓桿與口數計算
    lev = 6.0 if capital < 100000 else (3.5 if capital >= 3000000 else 4.75)
    exp = capital * lev
    lots = exp / (res['p'] * 1000)

    st.subheader(f"⚔️ 彈藥建議 (槓桿: {lev}x)")
    st.write(f"當前建議持有: **{round(lots, 1)} 口** (小0050期)")
else:
    st.error(f"📡 衛星連線異常：{res}")
    st.info("請確認 GitHub 的 requirements.txt 內容是否正確。")
