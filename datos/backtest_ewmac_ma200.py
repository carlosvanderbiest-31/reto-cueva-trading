"""
EWMAC + filtro MA200 — BTC, ETH, SOL
  Entrada : EWMA(fast) cruza por encima de EWMA(slow)
            Y close > MA200 del mismo timeframe
  Salida  : EWMA(fast) cruza por debajo de EWMA(slow)
            O close cae por debajo de MA200 (cierre forzado)
  Costes  : 0.15% roundtrip
  Split   : 70 IS / 30 OOS

MA200 en cada TF equivale a:
  4H  -> 200 x 4h  = ~33 dias
  1H  -> 200 x 1h  = ~8 dias
  15m -> 200 x 15m = ~2 dias  (filtro muy corto, se espera poco impacto)
"""

import pandas as pd
import os

COST_RT = 0.0015
SPLIT   = 0.70

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

def bt_ewmac_ma200(df, fast, slow, ma=200, cost=COST_RT):
    df = df.copy().reset_index(drop=True)
    spl = int(len(df) * SPLIT)

    df['ef']   = df['close'].ewm(span=fast, adjust=False).mean()
    df['es']   = df['close'].ewm(span=slow, adjust=False).mean()
    df['ma200']= df['close'].rolling(ma).mean()
    df['cx']   = (df['ef'] > df['es']).astype(int).diff()

    trades, state, ep, ei = [], 'FUERA', None, None
    pi = po = False

    for i in range(max(slow, ma) + 1, len(df)):
        r = df.loc[i]

        # ejecutar entrada pendiente (solo si precio sigue sobre MA200)
        if pi and state == 'FUERA':
            if r['close'] > r['ma200']:
                ep, ei, state = r['open'], i, 'DENTRO'
            pi = False

        # ejecutar salida pendiente
        if po and state == 'DENTRO':
            trades.append({'i': ei, 'pnl': (r['open'] - ep) / ep - cost, 'oos': ei >= spl})
            state, po = 'FUERA', False

        # salida forzada si precio cae bajo MA200
        if state == 'DENTRO' and r['close'] < r['ma200']:
            trades.append({'i': ei, 'pnl': (r['close'] - ep) / ep - cost, 'oos': ei >= spl})
            state = 'FUERA'

        # detectar senales EWMAC
        if state == 'FUERA'  and r['cx'] ==  1: pi = True
        if state == 'DENTRO' and r['cx'] == -1: po = True

    if state == 'DENTRO':
        trades.append({'i': ei, 'pnl': (df.iloc[-1]['close'] - ep) / ep - cost, 'oos': ei >= spl})
    return trades

BASE   = os.path.dirname(os.path.abspath(__file__))
PAIRS  = ['BTC', 'ETH', 'SOL']
TFS    = [('4H', '4h'), ('1H', '1h'), ('15m', '15m')]
COMBOS = [(8, 32), (16, 64), (32, 128)]

def load(pair, tf_file):
    path = os.path.join(BASE, f"{pair}USDT_{tf_file}.csv")
    df = pd.read_csv(path, parse_dates=['time'])
    for c in ['open', 'high', 'low', 'close']:
        df[c] = df[c].astype(float)
    return df.reset_index(drop=True)

print("Cargando y procesando...\n")

all_results = []
for pair in PAIRS:
    for tf_name, tf_file in TFS:
        df = load(pair, tf_file)
        for fast, slow in COMBOS:
            trades = bt_ewmac_ma200(df, fast, slow)
            oos    = [t['pnl'] for t in trades if t['oos']]
            m      = score4(oos)
            all_results.append({**m, 'pair': pair, 'tf': tf_name, 'fast': fast, 'slow': slow})

# ── tabla completa ─────────────────────────────────────────────────────────────
print(f"{'Par':<5} {'TF':<4} {'EWMAC':<10} {'FB':>7} {'Ops':>5} {'DD':>7} {'FB_nb':>7} {'Score':>6}  Veredicto")
print("-" * 80)

cur_pair = None
for r in all_results:
    if r['pair'] != cur_pair:
        if cur_pair is not None: print()
        cur_pair = r['pair']
    lbl = f"{r['fast']}/{r['slow']}"
    v   = ">>> APRUEBA <<<" if r['s'] == 4 else f"{r['s']}/4"
    print(f"{r['pair']:<5} {r['tf']:<4} EWMAC{lbl:<7} "
          f"{r['fb']:>7.3f} {r['n']:>5} {r['dd']:>6.1f}% "
          f"{r['fb_nb']:>7.3f} {r['s']:>4}/4   {v}")

# ── resumen ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
aprueba = [r for r in all_results if r['s'] == 4]
print(f"APRUEBA F1 (4/4): {len(aprueba)} de {len(all_results)} combinaciones")
if aprueba:
    print()
    print(f"{'Par':<5} {'TF':<4} {'EWMAC':<10} {'FB':>7} {'Ops':>5} {'DD':>7} {'FB_nb':>7}")
    print("-" * 55)
    for r in sorted(aprueba, key=lambda x: -x['fb']):
        lbl = f"{r['fast']}/{r['slow']}"
        print(f"{r['pair']:<5} {r['tf']:<4} EWMAC{lbl:<7} "
              f"{r['fb']:>7.3f} {r['n']:>5} {r['dd']:>6.1f}% {r['fb_nb']:>7.3f}")

casi = [r for r in all_results if r['s'] == 3]
if casi:
    print(f"\nCASI (3/4): {len(casi)} combinaciones")
    print(f"{'Par':<5} {'TF':<4} {'EWMAC':<10} {'FB':>7} {'Ops':>5} {'DD':>7} {'FB_nb':>7}  Falla")
    print("-" * 70)
    for r in sorted(casi, key=lambda x: -x['fb']):
        lbl = f"{r['fast']}/{r['slow']}"
        fails = " ".join([x for x, b in [
            ("DD", r['dd'] >= 20), ("FB", r['fb'] < 1.3),
            ("Ops", r['n'] < 30), ("FB_nb", r['fb_nb'] <= 1)] if b])
        print(f"{r['pair']:<5} {r['tf']:<4} EWMAC{lbl:<7} "
              f"{r['fb']:>7.3f} {r['n']:>5} {r['dd']:>6.1f}% {r['fb_nb']:>7.3f}  {fails}")

print("\nFIN.")
