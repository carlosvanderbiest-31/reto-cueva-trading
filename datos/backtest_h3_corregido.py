"""
H3 — backtests con lógica TIS correcta
  H3a: BTC 4H   — Pullback MA200, salida ruptura MAX7  (= H2, ahora con histórico completo)
  H3b: NAS100   — Cruce MA50/200  (necesita datos 15m — se corre en 1h como proxy)
  H3c: XAU 1D   — Pullback MA200, salida ruptura MAX7  (misma lógica que BTC)
  H3d: NDX 1D   — RSI(2) < 10 + MA200, salida MA5

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
    print(f"\n{'='*58}")
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

# ── datos ─────────────────────────────────────────────────────────────────────
def yf_get(ticker, start, interval="1d"):
    raw = yf.download(ticker, start=start, end="2026-10-27",
                      interval=interval, progress=False, auto_adjust=True)
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = raw[['Open','High','Low','Close']].rename(
        columns={'Open':'open','High':'high','Low':'low','Close':'close'})
    df = df.dropna().reset_index()
    df.columns = ['time','open','high','low','close']
    for c in ['open','high','low','close']:
        df[c] = df[c].astype(float)
    return df

print("Descargando datos...")
xau = yf_get("GC=F",  "2000-01-01", "1d")
ndx = yf_get("^NDX",  "2000-01-01", "1d")
btc = pd.read_csv(r"BTCUSDT_4h.csv", parse_dates=['time'])
for c in ['open','high','low','close']:
    btc[c] = btc[c].astype(float)
btc = btc.reset_index(drop=True)

for name, df in [("XAU 1D",xau),("NDX 1D",ndx),("BTC 4H",btc)]:
    print(f"  {name:<22} {len(df):>6} barras  "
          f"{str(df['time'].iloc[0])[:10]} / {str(df['time'].iloc[-1])[:10]}")

# ── rsi helper ────────────────────────────────────────────────────────────────
def rsi_calc(s, p):
    d  = s.diff()
    u  = d.clip(lower=0).ewm(com=p-1, min_periods=p).mean()
    dn = (-d.clip(upper=0)).ewm(com=p-1, min_periods=p).mean()
    return 100 - 100 / (1 + u / dn)

# ── estrategia A: pullback MA200, salida MAX7 (BTC / XAU) ────────────────────
def backtest_pullback_ma200(df, n=7, ma=200, stop_pct=0.02):
    """
    BUSCANDO: close < MIN7_prev AND close > MA200  →  ENTRADA_PENDIENTE
    DENTRO:   low <= STOP  →  salir al stop
              close > MAX7_prev  →  salir al cierre
    """
    df  = df.copy().reset_index(drop=True)
    spl = int(len(df) * SPLIT)
    df['ma200'] = df['close'].rolling(ma).mean()

    trades, state = [], 'BUSCANDO'
    entry_p = entry_i = stop_p = None
    pending = False

    for i in range(ma + n, len(df)):
        row  = df.loc[i]
        prev = df.loc[i-n : i-1]

        if pending:
            entry_p = row['open']
            entry_i = i
            stop_p  = entry_p * (1 - stop_pct)
            state   = 'DENTRO'
            pending = False

        if state == 'DENTRO':
            max7 = prev['high'].max()
            if row['low'] <= stop_p:
                pnl = (stop_p - entry_p) / entry_p - COST_RT
                trades.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= spl})
                state = 'BUSCANDO'
            elif row['close'] > max7:
                pnl = (row['close'] - entry_p) / entry_p - COST_RT
                trades.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= spl})
                state = 'BUSCANDO'

        if state == 'BUSCANDO':
            min7 = prev['low'].min()
            ma200 = row['ma200']
            if not pd.isna(ma200) and row['close'] < min7 and row['close'] > ma200:
                pending = True

    if state == 'DENTRO':
        pnl = (df.iloc[-1]['close'] - entry_p) / entry_p - COST_RT
        trades.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= spl})
    return trades

# ── estrategia B: cruce MA50/200 (NAS100) ─────────────────────────────────────
def backtest_ma_cross(df, fast=50, slow=200):
    """
    LARGO: MA_fast cruza sobre MA_slow  →  compra al cierre
    SALIDA: MA_fast cruza bajo MA_slow  →  vende al cierre
    """
    df  = df.copy().reset_index(drop=True)
    spl = int(len(df) * SPLIT)
    df['mf'] = df['close'].rolling(fast).mean()
    df['ms'] = df['close'].rolling(slow).mean()

    trades, state = [], 'FUERA'
    entry_p = entry_i = None

    for i in range(slow + 1, len(df)):
        prev, row = df.loc[i-1], df.loc[i]
        if pd.isna(prev['mf']) or pd.isna(prev['ms']): continue

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

# ── estrategia C: RSI(2) + MA200, salida MA5 (NDX 1D) ────────────────────────
def backtest_rsi2_ma200(df, rsi_p=2, rsi_lvl=10, ma_entry=200, ma_exit=5):
    """
    BUSCANDO: RSI(2) < 10 AND close > MA200  →  ENTRADA_PENDIENTE (compra al open siguiente)
    DENTRO:   close > MA5  →  SALIDA_PENDIENTE (vende al open siguiente)
    """
    df  = df.copy().reset_index(drop=True)
    spl = int(len(df) * SPLIT)
    df['ma200'] = df['close'].rolling(ma_entry).mean()
    df['ma5']   = df['close'].rolling(ma_exit).mean()
    df['rsi2']  = rsi_calc(df['close'], rsi_p)

    trades, state = [], 'BUSCANDO'
    entry_p = entry_i = None
    pend_in = pend_ex = False

    for i in range(ma_entry + 1, len(df)):
        row = df.loc[i]

        if pend_in and state == 'BUSCANDO':
            entry_p, entry_i = row['open'], i
            state = 'DENTRO'
            pend_in = False

        if pend_ex and state == 'DENTRO':
            pnl = (row['open'] - entry_p) / entry_p - COST_RT
            trades.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= spl})
            state = 'BUSCANDO'
            pend_ex = False

        if state == 'DENTRO':
            if not pd.isna(row['ma5']) and row['close'] > row['ma5']:
                pend_ex = True

        if state == 'BUSCANDO':
            if (not pd.isna(row['rsi2']) and not pd.isna(row['ma200'])
                    and row['rsi2'] < rsi_lvl and row['close'] > row['ma200']):
                pend_in = True

    if state == 'DENTRO':
        pnl = (df.iloc[-1]['close'] - entry_p) / entry_p - COST_RT
        trades.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= spl})
    return trades

# ── ejecutar ──────────────────────────────────────────────────────────────────
print("\nEjecutando backtests...\n")

show("H3a · BTC/USDT 4H · Pullback MA200, salida MAX7  (stop -2%)",
     backtest_pullback_ma200(btc))

print("\n" + "="*58)
print("  H3b · NAS100 15m · Cruce MA50/200")
print("  PENDIENTE — Yahoo Finance no entrega 15m con historia larga.")
print("  Exportar desde TradingView: NAS100, 15m, 4+ anos -> datos/NAS100_15m.csv")

show("H3c · XAU/USD 1D · Pullback MA200, salida MAX7  (stop -2%)",
     backtest_pullback_ma200(xau))

show("H3d · NDX/USD 1D · RSI(2)<10 + MA200, salida MA5",
     backtest_rsi2_ma200(ndx))

print("\nListo.")
