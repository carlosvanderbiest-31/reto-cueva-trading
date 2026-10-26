"""
Mega Cueva Tester — criterios TIS oficiales
Hipotesis: BTC/USDT 4H · EWMAC 8/32 + MA200 diaria + stop 3%

F1 Diseno       : PF>=1.30, ops>=30, DD<20%, PF_nb>1
F2 Walk-Forward : eficiencia>=0.50, anos positivos>=60%, peor caida en ano<20%
F3 Meseta       : peor vecino degrada <30%
F4 Monte Carlo  : caida peor 5% de 5000 caminos <25%
F5 Stress       : PF costes x2 >=1.10 y sin 2 mejores ops >=1.10
"""

import pandas as pd
import random
import os

COST_RT = 0.0015
SPLIT   = 0.70
N_MC    = 5000

BASE = os.path.dirname(os.path.abspath(__file__))

# ── helpers ───────────────────────────────────────────────────────────────────
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

def metrics4(p):
    if not p: return dict(fb=0, n=0, dd=100, fb_nb=0, pasa=0)
    fb = pf(p); n = len(p); dd = mdd(p)
    fb_nb = pf(sorted(p)[:-1]) if n > 1 else pf(p)
    return dict(fb=fb, n=n, dd=dd, fb_nb=fb_nb,
                pasa=sum([fb>=1.3, n>=30, dd<20, fb_nb>1]))

def ok(v): return "OK" if v else "XX"
def banner(t): print(f"\n{'#'*64}\n#  {t}\n{'#'*64}")

# ── datos ─────────────────────────────────────────────────────────────────────
def load_btc():
    df = pd.read_csv(os.path.join(BASE, 'BTCUSDT_4h.csv'), parse_dates=['time'])
    for c in ['open','high','low','close']:
        df[c] = df[c].astype(float)
    return df.reset_index(drop=True)

def add_dma200(df):
    df = df.copy().set_index('time')
    daily = df['close'].resample('1D').last().dropna()
    dma   = daily.rolling(200).mean().rename('dma200')
    df    = df.join(dma, how='left')
    df['dma200'] = df['dma200'].ffill()
    return df.reset_index()

print("Cargando BTC 4H...")
BTC = add_dma200(load_btc())
SPL = int(len(BTC) * SPLIT)
print(f"  {len(BTC)} barras  {str(BTC['time'].iloc[0])[:10]} / {str(BTC['time'].iloc[-1])[:10]}")
print(f"  Split: IS hasta barra {SPL} ({str(BTC['time'].iloc[SPL])[:10]})")

# ── motor ─────────────────────────────────────────────────────────────────────
def bt(df, fast=8, slow=32, stop_pct=0.03, cost=COST_RT, split_idx=None):
    df  = df.copy().reset_index(drop=True)
    spl = split_idx if split_idx is not None else int(len(df)*SPLIT)
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
            trades.append({'i': ei, 'pnl': (r['open']-ep)/ep - cost,
                           'oos': ei >= spl, 'time': str(df.loc[ei,'time'])})
            state, po = 'FUERA', False

        if state == 'DENTRO':
            if r['low'] <= sp:
                trades.append({'i': ei, 'pnl': (sp-ep)/ep - cost,
                               'oos': ei >= spl, 'time': str(df.loc[ei,'time'])})
                state = 'FUERA'
            elif r['close'] < dma:
                trades.append({'i': ei, 'pnl': (r['close']-ep)/ep - cost,
                               'oos': ei >= spl, 'time': str(df.loc[ei,'time'])})
                state = 'FUERA'
            elif r['cx'] == -1:
                po = True

        if state == 'FUERA' and r['cx'] == 1:
            pi = True

    if state == 'DENTRO':
        trades.append({'i': ei, 'pnl': (df.iloc[-1]['close']-ep)/ep - cost,
                       'oos': ei >= spl, 'time': str(df.loc[ei,'time'])})
    return trades

# ── F1 ────────────────────────────────────────────────────────────────────────
banner("F1 DISENO")
trades_base = bt(BTC, split_idx=SPL)
oos_base    = [t for t in trades_base if t['oos']]
is_base     = [t for t in trades_base if not t['oos']]
oos_pnl     = [t['pnl'] for t in oos_base]
is_pnl      = [t['pnl'] for t in is_base]
m = metrics4(oos_pnl)
print(f"  IS trades: {len(is_base)}  |  OOS trades: {m['n']}")
print(f"  FB      {m['fb']:.3f}  {ok(m['fb']>=1.3)}  (>=1.3)")
print(f"  Ops     {m['n']:>5}  {ok(m['n']>=30)}  (>=30)")
print(f"  DD      {m['dd']:.1f}%  {ok(m['dd']<20)}  (<20%)")
print(f"  FB_nb   {m['fb_nb']:.3f}  {ok(m['fb_nb']>1)}  (>1)")
v1 = "APRUEBA" if m['pasa']==4 else "NO APRUEBA"
print(f"  F1: {v1}  ({m['pasa']}/4)")

# ── F2 WALK-FORWARD ───────────────────────────────────────────────────────────
banner("F2 WALK-FORWARD  (IS=3a, OOS=1a, paso=1a)")

def f2_wf(df, bpy=365*6):   # 4H: ~6 barras/hora * 24h * 365d = 52560/year, pero usamos dias
    # calcular barras por ano en 4H: 6*24*365 = 52560 pero BTC opera 24/7
    # estimacion real: len(df)/anos_totales
    anos_total = (df['time'].iloc[-1] - df['time'].iloc[0]).days / 365.25
    bpy_real   = int(len(df) / anos_total)
    is_b       = bpy_real * 3
    oos_b      = bpy_real * 1
    win        = is_b + oos_b
    wf_r       = []
    start      = 0
    while start + win <= len(df):
        seg    = df.iloc[start:start+win].copy().reset_index(drop=True)
        all_t  = bt(seg, split_idx=is_b)
        is_p   = [t['pnl'] for t in all_t if not t['oos']]
        oos_p  = [t['pnl'] for t in all_t if t['oos']]
        pf_is  = pf(is_p); pf_oos = pf(oos_p)
        efic   = pf_oos / pf_is if pf_is > 0 else 0.0
        ano    = str(seg['time'].iloc[is_b])[:4]
        dd_oos = mdd(oos_p)
        wf_r.append({'ano': ano, 'pf_is': pf_is, 'pf_oos': pf_oos,
                     'efic': efic, 'pos': sum(oos_p) > 0, 'dd': dd_oos})
        start += oos_b
    return wf_r

wf = f2_wf(BTC)
print(f"  {'Ano':>5} {'PF IS':>7} {'PF OOS':>7} {'Efic':>6} {'Pos':>5} {'DD OOS':>7}")
print(f"  {'-'*46}")
n_pos = 0; worst_dd = 0.0; efic_list = []
for r in wf:
    tag = "SI" if r['pos'] else "NO"
    n_pos += int(r['pos'])
    worst_dd = max(worst_dd, r['dd'])
    if r['pf_is'] > 0: efic_list.append(r['efic'])
    print(f"  {r['ano']:>5} {r['pf_is']:>7.3f} {r['pf_oos']:>7.3f} "
          f"{r['efic']:>6.2f} {tag:>5} {r['dd']:>6.1f}%")

n = len(wf)
pct_pos  = n_pos / n * 100 if n else 0
efic_avg = sum(efic_list) / len(efic_list) if efic_list else 0
print(f"\n  Eficiencia promedio : {efic_avg:.2f}  {ok(efic_avg>=0.50)}  (>=0.50)")
print(f"  Anos positivos      : {n_pos}/{n} ({pct_pos:.0f}%)  {ok(pct_pos>=60)}  (>=60%)")
print(f"  Peor caida en ano   : {worst_dd:.1f}%  {ok(worst_dd<20)}  (<20%)")
c1=efic_avg>=0.50; c2=pct_pos>=60; c3=worst_dd<20
v2 = "APRUEBA" if (c1 and c2 and c3) else "NO APRUEBA"
print(f"  F2: {v2}")

# ── F3 MESETA ─────────────────────────────────────────────────────────────────
banner("F3 MESETA DE PARAMETROS")
base_fb = pf(oos_pnl)
# vecinos: fast +/-1, slow +/-8 (mantiene ratio ~1:4), stop +/-1%
grid = [
    {'fast': f, 'slow': s, 'stop': st}
    for f in [6, 7, 8, 9, 10]
    for s in [24, 28, 32, 36, 40]
    for st in [0.02, 0.03, 0.04]
]
print(f"  Caso base (8/32 stop 3%): FB {base_fb:.3f}")
print(f"  {'Params':<28} {'FB':>7} {'Delta%':>8}  Score")
print(f"  {'-'*55}")
worst_delta = 0.0
for p in grid:
    t    = bt(BTC, fast=p['fast'], slow=p['slow'], stop_pct=p['stop'], split_idx=SPL)
    oos  = [x['pnl'] for x in t if x['oos']]
    fb_v = pf(oos)
    delta = ((fb_v - base_fb) / base_fb * 100) if base_fb > 0 else -100
    worst_delta = min(worst_delta, delta)
    m2   = metrics4(oos)
    lbl  = f"f={p['fast']} s={p['slow']} st={int(p['stop']*100)}%"
    print(f"  {lbl:<28} {fb_v:>7.3f} {delta:>+7.1f}%  {m2['pasa']}/4")

print(f"\n  Peor vecino: {worst_delta:+.1f}%  {ok(worst_delta>-30)}  (umbral >-30%)")
v3 = "APRUEBA" if worst_delta > -30 else "NO APRUEBA"
print(f"  F3: {v3}")

# ── F4 MONTE CARLO ────────────────────────────────────────────────────────────
banner("F4 MONTE CARLO  (5000 caminos)")
random.seed(42)
n_oos = len(oos_base)
dd_list = []
for _ in range(N_MC):
    sample = random.choices(oos_base, k=n_oos)
    dd_list.append(mdd([t['pnl'] for t in sample]))
dd_list.sort()
p95  = dd_list[int(0.95 * N_MC)]
p50  = dd_list[N_MC // 2]
print(f"  {N_MC} caminos bootstrap con {n_oos} trades OOS")
print(f"  DD mediana     : {p50:.1f}%")
print(f"  DD peor 5%     : {p95:.1f}%  {ok(p95<25)}  (umbral <25%)")
v4 = "APRUEBA" if p95 < 25 else "NO APRUEBA"
print(f"  F4: {v4}")

# ── F5 STRESS ────────────────────────────────────────────────────────────────
banner("F5 STRESS")
# costes x2
t2   = bt(BTC, cost=COST_RT*2, split_idx=SPL)
oos2 = [x['pnl'] for x in t2 if x['oos']]
pf2  = pf(oos2)
print(f"  Costes x2:           PF {pf2:.3f}  {ok(pf2>=1.10)}  (>=1.10)")
# sin 2 mejores
sin2 = sorted(oos_pnl, reverse=True)[2:]
pfs2 = pf(sin2)
print(f"  Sin 2 mejores ops:   PF {pfs2:.3f}  {ok(pfs2>=1.10)}  (>=1.10)")
c5a = pf2 >= 1.10; c5b = pfs2 >= 1.10
v5 = "APRUEBA" if (c5a and c5b) else "NO APRUEBA"
print(f"  F5: {v5}")

# ── RESUMEN ───────────────────────────────────────────────────────────────────
fases = [v1, v2, v3, v4, v5]
n_ok  = sum(1 for f in fases if f == "APRUEBA")
print(f"\n{'='*64}")
print(f"HIPOTESIS: BTC/USDT 4H | EWMAC 8/32 | MA200 diaria | Stop 3%")
print(f"{'='*64}")
for i, (v, name) in enumerate(zip(fases,
        ['F1 Diseno','F2 Walk-Forward','F3 Meseta','F4 Monte Carlo','F5 Stress']), 1):
    marca = "APRUEBA" if v=="APRUEBA" else "NO APRUEBA"
    print(f"  {name:<20}: {marca}")
print(f"{'='*64}")
print(f"  PROTOCOLO: {n_ok}/5  {'>>> APRUEBA <<<' if n_ok >= 4 else 'NO APRUEBA'}")
print(f"{'='*64}")
print("\nFIN.")
