import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime

# ==========================================
# 🎖️ 指揮部核心配置
# ==========================================
TOKEN = "8137685110:AAFkDozi-FKMrLYJTcbxwb5Q8ishmJDm_u8"
CHAT_ID = "在此填入您的_CHAT_ID"  # 找 @userinfobot 取得

SYMBOL_MAIN = "0050.TW"
SYMBOL_TSMC = "2330.TW"

# ==========================================
# 📊 數據抓取與指標計算
# ==========================================
def get_signals():
    # 抓取 0050 與 台積電 數據
    df_0050 = yf.download(SYMBOL_MAIN, period="8mo", interval="1d")
    df_tsmc = yf.download(SYMBOL_TSMC, period="1mo", interval="1d")
    
    # 確保數據不為空
    if df_0050.empty or df_tsmc.empty: return None

    # --- 0050 指標計算 ---
    close = df_0050['Close'].iloc[-1]
    ma20 = df_0050['Close'].rolling(20).mean().iloc[-1]
    ma120 = df_0050['Close'].rolling(120).mean().iloc[-1]
    n20_h = df_0050['High'].rolling(20).max().shift(1).iloc[-1]
    n10_l = df_0050['Low'].rolling(10).min().shift(1).iloc[-1]
    bias_20 = ((close - ma20) / ma20) * 100

    # --- 台積電量能計算 ---
    v_curr = df_tsmc['Volume'].iloc[-1]
    v5ma = df_tsmc['Volume'].rolling(5).mean().iloc[-1]
    v_ratio = v_curr / v5ma

    return {
        "price": close, "ma20": ma20, "ma120": ma120,
        "n20h": n20_h, "n10l": n10_l, "bias": bias_20,
        "v_ratio": v_ratio, "v_curr": v_curr
    }

# ==========================================
# ⚡ 戰術判定引擎 (V3.1 校準版)
# ==========================================
def analyze_tactics(s):
    signal = "💤 靜默"
    action = "保持觀望，等待時機"
    alert_level = "INFO"

    # --- 1.6 倍量能熔斷 (僅限空頭) ---
    is_climax_16 = s['v_ratio'] > 1.6
    
    # --- 多頭判定 (Long) ---
    # 條件：>20MA 且 >=N20_H 且 量比>1.2 且 乖離<=5.5%
    if s['price'] > s['ma20'] and s['price'] >= s['n20h']:
        if s['v_ratio'] > 1.2 and s['bias'] <= 5.5:
            signal = "🔥 FIRE 多單點火"
            action = "建立 2 口小 0050 期 (3.5x 槓桿)\n若獲利 >2% 再加碼至 3 口 (6.0x)"
            alert_level = "SUCCESS"
        elif s['bias'] > 5.5:
            signal = "⚠️ 乖離過高"
            action = "等待拉回月線，禁止追高進場"

    # --- 空頭判定 (Short) ---
    # 條件：<20MA 且 <120MA 且 <=N10_L 且 量比>1.2 且 非1.6倍爆量
    elif s['price'] < s['ma20'] and s['price'] < s['ma120'] and s['price'] <= s['n10l']:
        if is_climax_16:
            signal = "🚫 禁止放空"
            action = "台積電量能爆表 (1.6x)，疑有竭盡性拋售或護盤，嚴禁追空！"
        elif s['v_ratio'] > 1.2:
            signal = "💣 ATTACK 空單突擊"
            action = "建立 2 口小 0050 期 (反手空頭 3.5x)"
            alert_level = "WARNING"

    # --- 出場判定 ---
    # 多單出場：破 20MA
    if s['price'] < s['ma20']:
        signal = "🛑 RETREAT 多單撤退"
        action = "收盤破 20MA，全軍平倉，保護本金！"
        alert_level = "CRITICAL"
    
    # 空單出場額外條件：1.6 倍爆量無條件出場
    if is_climax_16:
        signal = "🏳️ 空單撤退 (1.6x 熔斷)"
        action = "台積電放量 1.6 倍，空單立即無條件平倉獲利落袋！"
        alert_level = "CRITICAL"

    return signal, action, alert_level

# ==========================================
# 📡 Telegram 通訊模組
# ==========================================
async def send_command_center_report():
    data = get_signals()
    if not data: return
    
    sig, act, lvl = analyze_tactics(data)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = (
        f"🎖️ Trinity V3.1 雲端指揮部\n"
        f"⏰ 報時：{now}\n"
        f"----------------------------\n"
        f"【當前狀態】：{sig}\n"
        f"【戰術動作】：{act}\n"
        f"----------------------------\n"
        f"📍 0050 價位：{data['price']:.2f}\n"
        f"📉 20MA 位階：{data['ma20']:.2f}\n"
        f"🏰 半年線位：{data['ma120']:.2f}\n"
        f"📈 20日高點：{data['n20h']:.2f}\n"
        f"📊 2330 量比：{data['v_ratio']:.2f}x\n"
        f"⚠️ 乖離率：{data['bias']:.2f}%\n"
        f"----------------------------\n"
        f"副官小佛提醒：邊走邊看，紀律點火。"
    )
    
    print(f"[{now}] 掃描完成，目前狀態: {sig}")
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=report)

if __name__ == "__main__":
    print("🚀 Trinity V3.1 指揮部正式啟動...")
    asyncio.run(send_command_center_report())

