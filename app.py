import yfinance as yf
import pandas as pd
import numpy as np

def run_trinity_v8c_31_unrealized():
    print("📡 啟動 Trinity V8.C 3.1：2020-2026 全紀錄 (校準版：安太座機制 + 雙向乖離限制)")

    # 1. 數據下載
    start_d, end_d = "2019-06-01", "2026-02-21"
    s50 = yf.download("0050.TW", start=start_d, end=end_d, auto_adjust=True)
    s2330 = yf.download("2330.TW", start=start_d, end=end_d, auto_adjust=True)

    if isinstance(s50.columns, pd.MultiIndex): s50.columns = s50.columns.get_level_values(0)
    if isinstance(s2330.columns, pd.MultiIndex): s2330.columns = s2330.columns.get_level_values(0)

    df = pd.DataFrame(index=s50.index)
    df['0050_C'], df['0050_H'], df['0050_L'] = s50['Close'], s50['High'], s50['Low']
    df['2330_V'] = s2330['Volume']

    # 2. 指標計算
    df['20MA'] = df['0050_C'].rolling(20).mean()
    df['120MA'] = df['0050_C'].rolling(120).mean()
    df['N20_H'] = df['0050_H'].shift(1).rolling(20).max()
    df['N10_L'] = df['0050_L'].shift(1).rolling(10).min()
    df['V5MA_2330'] = df['2330_V'].rolling(5).mean()
    df['Bias_20MA'] = (df['0050_C'] - df['20MA']) / df['20MA']
    df = df.ffill().dropna()

    # 3. 戰略參數
    test_start = '2020-01-01'
    capital = 30000.0
    total_invested = capital
    tai_zuo_fund = 0.0  # 重新命名：安太座金庫
    withdrawn = False

    pos, entry_p, add_p, entry_date = 0, 0.0, 0.0, None
    last_m, is_full = -1, False
    lev1, lev2 = 0.0, 0.0
    logs = []

    # 4. 戰場迴圈
    for date, row in df.loc[test_start:].iterrows():
        if date.month != last_m:
            capital += 10000.0; total_invested += 10000.0; last_m = date.month

        if capital >= 1000000 and not withdrawn:
            tai_zuo_fund = total_invested; capital -= tai_zuo_fund; withdrawn = True
            logs.append({'進場日期': date.date(), '出場日期': '-', '方向': '💎', '進場價': '-', '出場價': '-', '報酬率': '-', '資產': int(capital), '備註': f'安太座抽回 {int(tai_zuo_fund):,}'})

        p, ma20, v_ratio = row['0050_C'], row['20MA'], row['2330_V'] / row['V5MA_2330']
        total_wealth = capital + tai_zuo_fund

        if pos != 0:
            if not is_full:
                move = (p - entry_p)/entry_p if pos == 1 else (entry_p - p)/entry_p
                if move >= 0.02: is_full = True; add_p = p

            exit_f = False
            # 多單標準：跌破 20MA
            if pos == 1 and row['0050_C'] < ma20: exit_f = True
            # 空單標準：1.6x 優先觸發，或 20MA 站回
            if pos == -1:
                if v_ratio > 1.6 or row['0050_C'] > ma20: exit_f = True
            
            if exit_f:
                exit_price = p
                if total_wealth < 100000:
                    total_roi = (exit_price - entry_p) / entry_p * lev1 * pos
                else:
                    roi1 = (exit_price - entry_p) / entry_p * lev1 * 0.5 * pos
                    actual_add_p = add_p if is_full else p
                    roi2 = (exit_price - actual_add_p) / actual_add_p * lev2 * 0.5 * pos
                    total_roi = roi1 + (roi2 if is_full else 0)

                capital += (capital * total_roi)
                logs.append({
                    '進場日期': entry_date.date(), '出場日期': date.date(),
                    '方向': '多' if pos==1 else '空', '進場價': round(entry_p, 2),
                    '出場價': round(exit_price, 2), '報酬率': f"{round(total_roi*100, 2)}%",
                    '資產': int(capital), '備註': '1.6x熔斷' if (pos==-1 and v_ratio > 1.6) else ''
                })
                pos, is_full = 0, False

        if pos == 0:
            vol_f = v_ratio > 1.2
            # 多單判定
            if p > ma20 and p >= row['N20_H'] and vol_f and row['Bias_20MA'] <= 0.055:
                pos, entry_p, entry_date = 1, p, date
                if total_wealth < 100000: lev1, lev2, is_full, add_p = 6.0, 6.0, True, p
                elif total_wealth < 3000000: lev1, lev2, is_full = 3.5, 6.0, False
                else: lev1, lev2, is_full = 3.5, 3.5, False
            
            # 空單判定 (同步校準：包含 Bias >= -5.5%)
            elif p < ma20 and p < row['120MA'] and p <= row['N10_L'] and vol_f and v_ratio <= 1.6 and row['Bias_20MA'] >= -0.055:
                pos, entry_p, entry_date = -1, p, date
                if total_wealth < 100000: lev1, lev2, is_full, add_p = 6.0, 6.0, True, p
                elif total_wealth < 3000000: lev1, lev2, is_full = 3.5, 6.0, False
                else: lev1, lev2, is_full = 3.5, 3.5, False

    # 4.5 捕捉未平倉部位
    if pos != 0:
        last_row = df.iloc[-1]
        last_p = last_row['0050_C']
        if total_wealth < 100000:
            unrealized_roi = (last_p - entry_p) / entry_p * lev1 * pos
        else:
            ur1 = (last_p - entry_p) / entry_p * lev1 * 0.5 * pos
            actual_add_p = add_p if is_full else last_p
            ur2 = (last_p - actual_add_p) / actual_add_p * lev2 * 0.5 * pos
            unrealized_roi = ur1 + (ur2 if is_full else 0)
        
        capital_with_float = capital + (capital * unrealized_roi)
        logs.append({
            '進場日期': entry_date.date(), '出場日期': '持有中',
            '方向': '多' if pos==1 else '空', '進場價': round(entry_p, 2),
            '出場價': round(last_p, 2), '報酬率': f"{round(unrealized_roi*100, 2)}%",
            '資產': int(capital_with_float), '備註': '🚩 未平倉部位 (現價估值)'
        })

    res = pd.DataFrame(logs)
    return res
