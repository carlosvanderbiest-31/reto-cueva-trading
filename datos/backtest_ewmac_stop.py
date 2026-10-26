"""
EWMAC + MA200 diaria + stop fijo — BTC, ETH, SOL
  Entrada : EWMA(fast) cruza sobre EWMA(slow) Y close > MA200_diaria
  Salida  : cruce bajista EWMA | close < MA200_diaria | low <= stop (entry * (1-stop%))
  Stops   : 3%, 5%, 8%, 10%, 15%
  TFs     : 4H, 1H  (15m descartado)
  Costes  : 0.15% roundtrip  |  Split 70/30
"""

import pandas as pd
import os

COST_RT = 0.0015
SPLIT   = 0.70
STOPS   = [0.03, 0.05, 0.08, 0.10, 0.15]

def pf(p):
    w = sum(x for x in p if x > 0)
    l = abs(sum(x for x in p if x <= 0))
    return w / l if l > 0 else (float('inf') if w > 0 else 0.0)

def mdd(p):
    eq, pk, worst = 1.0, 1.0, 0.0
    for x in p:
        eq *= (1 + x); pk = max(pk, eq)
        worst = max(worst, (pk - eq) / pk)
    return worst * 100

def score4(p):
    if not p: return dict(fb=0, n=0, dd=100, fb_nb=0, s=0)
    fb = pf(p); n = len(p); dd = mdd(p)
    fb_nb = pf(sorted(p)[:-1]) if n > 1 else fb
    s = sum([fb >= 1.3, n >= 30, dd < 20, fb_nb > 1])
    return dict(fb=fb, n=n, dd=dd, fb_nb=fb_nb, s=s)

def add_daily_ma200(df):
    df = df.copy().set_index('time')
    daily = df['close'].resample('1D').last().dropna()
    dma   = daily.rolling(200).mean().rename('dma200')
    df    = df.join(dma, how='left')
    df['dma200'] = df['dma200'].ffill()
    return df.reset_index()

def bt(df, fast, slow, stop_pct, cost=COST_RT):
    df  = df.copy().reset_index(drop=True)
    spl = int(len(df) * SPLIT)
    df['ef'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['es'] = df['close'].ewm(span=slow, adjust=False).mean()
    df['cx'] = (df['ef'] > df['es']).astype(int).diff()

    trades, state, ep, ei, sp = [], 'FUERA', None, None, None
    pi = po = False

    for i in range(slow + 1, len(df)):
        r   = df.loc[i]
        dma = r['dma200']
        if pd.isna(dma): continue

        if pi and state == 'FUERA':
            if r['close'] > dma:
                ep, ei = r['open'], i
                sp     = ep * (1 - stop_pct)
                state  = 'DENTRO'
            pi = False

        if po and state == 'DENTRO':
            trades.append({'i': ei, 'pnl': (r['open'] - ep) / ep - cost, 'oos': ei >= spl})
            state, po = 'FUERA', False

        if state == 'DENTRO':
            # stop fijo
            if r['low'] <= sp:
                trades.append({'i': ei, 'pnl': (sp - ep) / ep - cost, 'oos': ei >= spl})
                state = 'FUERA'
            # salida por MA200 diaria
            elif r['close'] < dma:
                trades.append({'i': ei, 'pnl': (r['close'] - ep) / ep - cost, 'oos': ei >= spl})
                state = 'FUERA'
            elif r['cx'] == -1:
                po = True

        if state == 'FUERA' and r['cx'] == 1:
            pi = True

    if state == 'DENTRO':
        trades.append({'i': ei, 'pnl': (df.iloc[-1]['close'] - ep) / ep - cost, 'oos': ei >= spl})
    return trades

BASE   = os.path.dirname(os.path.abspath(__file__))
PAIRS  = ['BTC', 'ETH', 'SOL']
TFS    = [('4H', '4h'), ('1H', '1h')]
COMBOS = [(8, 32), (16, 64), (32, 128)]

def load(pair, tf_file):
    path = os.path.join(BASE, f"{pair}USDT_{tf_file}.csv")
    df = pd.read_csv(path, parse_dates=['time'])
    for c in ['open', 'high', 'low', 'close']:
        df[c] = df[c].astype(float)
    return df.reset_index(drop=True)

print("Procesando...\n")

# precarga y MA200 diaria
dfs = {}
for pair in PAIRS:
    for tf_name, tf_file in TFS:
        dfs[(pair, tf_name)] = add_daily_ma200(load(pair, tf_file))

all_r = []
for pair in PAIRS:
    for tf_name, _ in TFS:
        df = dfs[(pair, tf_name)]
        for fast, slow in COMBOS:
            for stp in STOPS:
                trades = bt(df, fast, slow, stp)
                oos    = [t['pnl'] for t in trades if t['oos']]
                m      = score4(oos)
                all_r.append({**m, 'pair': pair, 'tf': tf_name,
                               'fast': fast, 'slow': slow, 'stop': stp})

# ── solo los que aprueban ──────────────────────────────────────────────────────
aprueba = [r for r in all_r if r['s'] == 4]
casi    = [r for r in all_r if r['s'] == 3]

print(f"Total combinaciones: {len(all_r)}")
print(f"Aprueban 4/4 : {len(aprueba)}")
print(f"Casi    3/4  : {len(casi)}")

if aprueba:
    print(f"\n{'='*80}")
    print("APRUEBA F1 (4/4):")
    print(f"{'Par':<5} {'TF':<4} {'EWMAC':<10} {'Stop':>6} {'FB':>7} {'Ops':>5} {'DD':>7} {'FB_nb':>7}")
    print("-" * 60)
    for r in sorted(aprueba, key=lambda x: -x['fb']):
        lbl = f"{r['fast']}/{r['slow']}"
        print(f"{r['pair']:<5} {r['tf']:<4} EWMAC{lbl:<7} "
              f"{r['stop']*100:>5.0f}%  "
              f"{r['fb']:>7.3f} {r['n']:>5} {r['dd']:>6.1f}% {r['fb_nb']:>7.3f}")

print(f"\n{'='*80}")
print("CASI (3/4) — los 15 mejores por FB:")
print(f"{'Par':<5} {'TF':<4} {'EWMAC':<10} {'Stop':>6} {'FB':>7} {'Ops':>5} {'DD':>7} {'FB_nb':>7}  Falla")
print("-" * 75)
for r in sorted(casi, key=lambda x: -x['fb'])[:15]:
    lbl   = f"{r['fast']}/{r['slow']}"
    fails = " ".join([x for x, b in [
        ("DD",  r['dd']    >= 20), ("FB",    r['fb']    < 1.3),
        ("Ops", r['n']     <  30), ("FB_nb", r['fb_nb'] <= 1)] if b])
    print(f"{r['pair']:<5} {r['tf']:<4} EWMAC{lbl:<7} "
          f"{r['stop']*100:>5.0f}%  "
          f"{r['fb']:>7.3f} {r['n']:>5} {r['dd']:>6.1f}% {r['fb_nb']:>7.3f}  {fails}")

# ── tabla BTC completa para ver la evolucion por stop ─────────────────────────
print(f"\n{'='*80}")
print("BTC 4H EWMAC8/32 — evolucion por nivel de stop:")
print(f"{'Stop':>6} {'FB':>7} {'Ops':>5} {'DD':>7} {'FB_nb':>7} {'Score':>6}")
print("-" * 45)
sub = [r for r in all_r if r['pair']=='BTC' and r['tf']=='4H'
       and r['fast']==8 and r['slow']==32]
for r in sorted(sub, key=lambda x: x['stop']):
    mk = " <-- APRUEBA" if r['s']==4 else ""
    print(f"{r['stop']*100:>5.0f}%  {r['fb']:>7.3f} {r['n']:>5} "
          f"{r['dd']:>6.1f}% {r['fb_nb']:>7.3f} {r['s']:>4}/4{mk}")

print(f"\n{'='*80}")
print("SOL 4H EWMAC16/64 — evolucion por nivel de stop:")
print(f"{'Stop':>6} {'FB':>7} {'Ops':>5} {'DD':>7} {'FB_nb':>7} {'Score':>6}")
print("-" * 45)
sub = [r for r in all_r if r['pair']=='SOL' and r['tf']=='4H'
       and r['fast']==16 and r['slow']==64]
for r in sorted(sub, key=lambda x: x['stop']):
    mk = " <-- APRUEBA" if r['s']==4 else ""
    print(f"{r['stop']*100:>5.0f}%  {r['fb']:>7.3f} {r['n']:>5} "
          f"{r['dd']:>6.1f}% {r['fb_nb']:>7.3f} {r['s']:>4}/4{mk}")

print("\nFIN.")
