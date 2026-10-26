"""
EWMAC BTC — hipotesis estilo Carver
  Entrada : EWMA(fast) cruza por encima de EWMA(slow) -> compra al open siguiente
  Salida  : EWMA(fast) cruza por debajo de EWMA(slow) -> vende al open siguiente
  Costes  : 0.15% roundtrip
  Split   : 70% IS / 30% OOS
  Activo  : BTCUSDT — 4H, 1H, 15m (CSVs en datos/)

Combinaciones:
  EWMAC 8/32  — rapida
  EWMAC 16/64 — media (Carver referencia)
  EWMAC 32/128 — lenta
"""

import pandas as pd
import numpy as np
import os

COST_RT = 0.0015
SPLIT   = 0.70

# ── helpers ───────────────────────────────────────────────────────────────────
def pf(pnls):
    w = sum(p for p in pnls if p > 0)
    l = abs(sum(p for p in pnls if p <= 0))
    return w / l if l > 0 else (float('inf') if w > 0 else 0.0)

def mdd(pnls):
    eq, peak, worst = 1.0, 1.0, 0.0
    for p in pnls:
        eq *= (1 + p); peak = max(peak, eq)
        worst = max(worst, (peak - eq) / peak)
    return worst * 100

def veredicto(pnls):
    if not pnls:
        return dict(fb=0, n=0, dd=100, fb_nb=0, score=0)
    fb   = pf(pnls)
    n    = len(pnls)
    dd   = mdd(pnls)
    nb   = sorted(pnls)[:-1] if n > 1 else pnls
    fb_nb = pf(nb)
    score = sum([fb >= 1.3, n >= 30, dd < 20, fb_nb > 1])
    return dict(fb=fb, n=n, dd=dd, fb_nb=fb_nb, score=score)

# ── motor EWMAC ───────────────────────────────────────────────────────────────
def backtest_ewmac(df, fast, slow, cost=COST_RT):
    df  = df.copy().reset_index(drop=True)
    spl = int(len(df) * SPLIT)

    df['ema_f'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_s'] = df['close'].ewm(span=slow, adjust=False).mean()
    df['sig']   = (df['ema_f'] > df['ema_s']).astype(int)
    df['cross'] = df['sig'].diff()  # +1 cruce alcista, -1 cruce bajista

    trades, state = [], 'FUERA'
    ep = ei = None
    pend_in = pend_out = False

    for i in range(slow + 1, len(df)):
        row = df.loc[i]

        # ejecutar entrada pendiente
        if pend_in and state == 'FUERA':
            ep, ei = row['open'], i
            state = 'DENTRO'
            pend_in = False

        # ejecutar salida pendiente
        if pend_out and state == 'DENTRO':
            pnl = (row['open'] - ep) / ep - cost
            trades.append({'i': ei, 'pnl': pnl, 'oos': ei >= spl})
            state = 'FUERA'
            pend_out = False

        # detectar senales
        if state == 'FUERA' and row['cross'] == 1:
            pend_in = True
        if state == 'DENTRO' and row['cross'] == -1:
            pend_out = True

    # cerrar posicion abierta al final
    if state == 'DENTRO':
        pnl = (df.iloc[-1]['close'] - ep) / ep - cost
        trades.append({'i': ei, 'pnl': pnl, 'oos': ei >= spl})

    return trades

# ── cargar CSVs ───────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))

def load_csv(fname):
    path = os.path.join(BASE, fname)
    df = pd.read_csv(path, parse_dates=['time'])
    for c in ['open', 'high', 'low', 'close']:
        df[c] = df[c].astype(float)
    return df.reset_index(drop=True)

print("Cargando datos BTC...")
tfs = {
    '4H' : load_csv('BTCUSDT_4h.csv'),
    '1H' : load_csv('BTCUSDT_1h.csv'),
    '15m': load_csv('BTCUSDT_15m.csv'),
}
for tf, df in tfs.items():
    print(f"  BTC {tf:>3}: {len(df):>7} barras  "
          f"{str(df['time'].iloc[0])[:10]} / {str(df['time'].iloc[-1])[:10]}")

# ── ejecutar todas las combinaciones ─────────────────────────────────────────
combos = [(8, 32), (16, 64), (32, 128)]
ok = lambda v: "OK" if v else "XX"

print()
print(f"{'TF':>5}  {'EWMAC':>9}  {'FB':>7}  {'Ops':>5}  {'DD':>7}  {'FB_nb':>7}  {'Score':>7}  Veredicto")
print(f"{'-'*75}")

results = []
for tf_name, df in tfs.items():
    for fast, slow in combos:
        trades = backtest_ewmac(df, fast, slow)
        oos    = [t['pnl'] for t in trades if t['oos']]
        m      = veredicto(oos)
        v      = "APRUEBA" if m['score'] == 4 else "NO APRUEBA"
        label  = f"EWMAC{fast}/{slow}"
        print(f"  {tf_name:>3}  {label:>9}  "
              f"{m['fb']:>7.3f}  {m['n']:>5}  {m['dd']:>6.1f}%  "
              f"{m['fb_nb']:>7.3f}  {m['score']:>4}/4   {v}")
        results.append({**m, 'tf': tf_name, 'fast': fast, 'slow': slow, 'label': label})
    print()

# ── resumen final ─────────────────────────────────────────────────────────────
print(f"{'='*75}".replace('=','='))
print("RESUMEN — estrategias que aprueban F1 (4/4):")
aprueba = [r for r in results if r['score'] == 4]
if aprueba:
    for r in aprueba:
        print(f"  {r['tf']:>3}  {r['label']:>9}  "
              f"FB {r['fb']:.3f}  {r['n']} ops  DD {r['dd']:.1f}%")
else:
    print("  Ninguna combinacion aprueba los 4 criterios.")

print("\nFIN.")
