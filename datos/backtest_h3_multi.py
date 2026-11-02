"""
Backtest múltiple — 5 hipótesis H3
  H3a: BTC 4H  — Ruptura min/max 7 velas (largo)
  H3b: NAS100 Mensual — Cruce MA 50/200
  H3c: XAU Diario  — Ruptura min/max 7 velas (igual que BTC)
  H3d: NDX 1D  — Connors RSI < 10 / > 70
  H3e: NDX 1D  — Ruptura min/max 7 velas (igual que BTC/XAU)

Costes: 0.15% roundtrip | Split 70/30
"""

import pandas as pd
import numpy as np
import yfinance as yf

COST_RT = 0.0015
SPLIT   = 0.70

# ── helpers ──────────────────────────────────────────────────────────────────
def profit_factor(pnls):
    w = sum(p for p in pnls if p > 0)
    l = abs(sum(p for p in pnls if p <= 0))
    return w / l if l > 0 else (float('inf') if w > 0 else 0.0)

def max_dd(pnls):
    eq, peak, worst = 1.0, 1.0, 0.0
    for p in pnls:
        eq *= (1 + p)
        peak = max(peak, eq)
        worst = max(worst, (peak - eq) / peak)
    return worst * 100

def show(label, trades):
    oos  = [t for t in trades if t['oos']]
    pnls = [t['pnl'] for t in oos]
    print(f"\n{'='*56}")
    print(f"  {label}")
    print(f"  Trades totales: {len(trades)}  |  OOS: {len(oos)}")
    if not pnls:
        print("  VEREDICTO: 0/4  NO APRUEBA (sin operaciones OOS)")
        return
    fb    = profit_factor(pnls)
    n     = len(pnls)
    dd    = max_dd(pnls)
    nb    = sorted(pnls)[:-1] if n > 1 else pnls
    fb_nb = profit_factor(nb)
    ok    = lambda v: "OK" if v else "XX"
    pasa  = sum([fb >= 1.3, n >= 30, dd < 20, fb_nb > 1])
    wins  = sum(1 for p in pnls if p > 0)
    print(f"  FB            {fb:6.3f}  {ok(fb>=1.3)}  (>=1.3)")
    print(f"  Operaciones   {n:6d}  {ok(n>=30)}  (>=30)")
    print(f"  Caida max     {dd:5.1f}%  {ok(dd<20)}  (<20%)")
    print(f"  FB sin mejor  {fb_nb:6.3f}  {ok(fb_nb>1)}  (>1)")
    print(f"  Ganadoras     {wins}/{n} ({wins/n*100:.0f}%)")
    print(f"  VEREDICTO: {pasa}/4  {'>>> APRUEBA <<<' if pasa==4 else 'NO APRUEBA'}")

# ── descargar datos ───────────────────────────────────────────────────────────
print("Descargando datos de Yahoo Finance...")

def yf_download(ticker, start, interval):
    raw = yf.download(ticker, start=start, end="2026-10-27",
                      interval=interval, progress=False, auto_adjust=True)
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw = raw[['Open','High','Low','Close']].rename(
        columns={'Open':'open','High':'high','Low':'low','Close':'close'})
    raw = raw.dropna().reset_index()
    raw.columns = ['time','open','high','low','close']
    for c in ['open','high','low','close']:
        raw[c] = raw[c].astype(float)
    return raw

ndx_d = yf_download("^NDX",  "2000-01-01", "1d")
ndx_m = yf_download("^NDX",  "1990-01-01", "1mo")
xau_d = yf_download("GC=F",  "2000-01-01", "1d")
btc   = pd.read_csv(r"BTCUSDT_4h.csv", parse_dates=['time'])
for c in ['open','high','low','close']:
    btc[c] = btc[c].astype(float)
btc = btc.reset_index(drop=True)

for name, df in [("NDX diario",ndx_d),("NDX mensual",ndx_m),
                 ("XAU diario",xau_d),("BTC 4H",btc)]:
    print(f"  {name:<14} {len(df):>5} barras  "
          f"{str(df['time'].iloc[0])[:10]} / {str(df['time'].iloc[-1])[:10]}")

# ── backtest ruptura 7 velas ──────────────────────────────────────────────────
def backtest_breakout7(df, n_bars=7):
    df  = df.copy().reset_index(drop=True)
    spl = int(len(df) * SPLIT)
    N   = n_bars

    trades, state = [], 'BUSCANDO'
    entry_p = entry_i = None
    pending = False

    for i in range(N, len(df)):
        row  = df.loc[i]
        prev = df.loc[i-N : i-1]
        max7 = prev['high'].max()
        min7 = prev['low'].min()

        # entrada diferida al open de esta vela
        if pending:
            entry_p = row['open']
            entry_i = i
            state   = 'DENTRO'
            pending = False

        if state == 'DENTRO':
            if row['close'] < min7:
                pnl = (row['close'] - entry_p) / entry_p - COST_RT
                trades.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= spl})
                state = 'BUSCANDO'

        if state == 'BUSCANDO':
            if row['close'] > max7:
                pending = True

    # cierra posición abierta al final
    if state == 'DENTRO':
        pnl = (df.iloc[-1]['close'] - entry_p) / entry_p - COST_RT
        trades.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= spl})

    return trades

# ── backtest cruce MA ─────────────────────────────────────────────────────────
def backtest_ma_cross(df, fast=50, slow=200):
    df  = df.copy().reset_index(drop=True)
    spl = int(len(df) * SPLIT)
    df['mf'] = df['close'].rolling(fast).mean()
    df['ms'] = df['close'].rolling(slow).mean()

    trades, state = [], 'FUERA'
    entry_p = entry_i = None

    for i in range(slow + 1, len(df)):
        prev, row = df.loc[i-1], df.loc[i]

        if state == 'DENTRO':
            if prev['mf'] >= prev['ms'] and row['mf'] < row['ms']:
                pnl = (row['close'] - entry_p) / entry_p - COST_RT
                trades.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= spl})
                state = 'FUERA'

        if state == 'FUERA':
            if prev['mf'] <= prev['ms'] and row['mf'] > row['ms']:
                entry_p, entry_i = row['close'], i
                state = 'DENTRO'

    if state == 'DENTRO':
        pnl = (df.iloc[-1]['close'] - entry_p) / entry_p - COST_RT
        trades.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= spl})

    return trades

# ── backtest connors rsi ──────────────────────────────────────────────────────
def rsi_calc(s, p):
    d  = s.diff()
    u  = d.clip(lower=0).ewm(com=p-1, min_periods=p).mean()
    dn = (-d.clip(upper=0)).ewm(com=p-1, min_periods=p).mean()
    return 100 - 100 / (1 + u / dn)

def calc_crsi(close):
    rsi3 = rsi_calc(close, 3)

    streak = pd.Series(0.0, index=close.index)
    for i in range(1, len(close)):
        if close.iat[i] > close.iat[i-1]:
            streak.iat[i] = max(1.0, streak.iat[i-1] + 1)
        elif close.iat[i] < close.iat[i-1]:
            streak.iat[i] = min(-1.0, streak.iat[i-1] - 1)

    streak_rsi = rsi_calc(streak, 2)
    roc = close.pct_change()
    pct_rank = roc.rolling(100).apply(
        lambda x: float((x[:-1] < x[-1]).sum()) / 99.0 * 100.0, raw=True)

    return (rsi3 + streak_rsi + pct_rank) / 3.0

def backtest_connors(df, buy=10, sell=70, stop_pct=0.10):
    df  = df.copy().reset_index(drop=True)
    spl = int(len(df) * SPLIT)
    df['crsi'] = calc_crsi(df['close'])

    trades, state = [], 'BUSCANDO'
    entry_p = entry_i = stop = None
    pend_in = pend_ex = False

    for i in range(102, len(df)):
        row = df.loc[i]

        if pend_in and state == 'BUSCANDO':
            entry_p = row['open']
            entry_i = i
            stop    = entry_p * (1 - stop_pct)
            state   = 'DENTRO'
            pend_in = False

        if pend_ex and state == 'DENTRO':
            pnl = (row['open'] - entry_p) / entry_p - COST_RT
            trades.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= spl})
            state   = 'BUSCANDO'
            pend_ex = False

        if state == 'DENTRO':
            if row['low'] <= stop:
                pnl = (stop - entry_p) / entry_p - COST_RT
                trades.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= spl})
                state = 'BUSCANDO'
            elif not pd.isna(row['crsi']) and row['crsi'] > sell:
                pend_ex = True

        if state == 'BUSCANDO':
            if not pd.isna(row['crsi']) and row['crsi'] < buy:
                pend_in = True

    return trades

# ── ejecutar ─────────────────────────────────────────────────────────────────
print("\nEjecutando backtests...\n")

show("H3a · BTC/USDT 4H · Ruptura min/max 7 velas",
     backtest_breakout7(btc))

show("H3b · NAS100 Mensual · Cruce MA 50/200",
     backtest_ma_cross(ndx_m, fast=50, slow=200))

show("H3c · XAU/USD Diario · Ruptura min/max 7 velas",
     backtest_breakout7(xau_d))

show("H3d · NDX/USD 1D · Connors RSI <10 compra />70 vende  (stop 10%)",
     backtest_connors(ndx_d))

show("H3e · NDX/USD 1D · Ruptura min/max 7 velas",
     backtest_breakout7(ndx_d))

print("\nListo.")
