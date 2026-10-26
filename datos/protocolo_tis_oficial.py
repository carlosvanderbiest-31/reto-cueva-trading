"""
Mega Cueva Tester — criterios EXACTOS del sitio TIS oficial
  F1 Diseno       : PF >= 1.30, ops >= 30, DD < 20%, PF_nb > 1
  F2 Walk-Forward : eficiencia OOS/IS >= 0.50
                    anos en positivo >= 60%
                    peor caida en un ano < 20%
  F3 Meseta       : peor vecino (parametro adyacente) degrada < 30%
  F4 Monte Carlo  : caida maxima peor 5% de 5000 caminos < 25%
  F5 Stress       : PF costes x2 >= 1.10
                    PF sin las 2 mejores operaciones >= 1.10

Aplicado a:
  H3c : XAU/USD 1D  - Pullback MA200, salida MAX7 (stop -2%)
  H3d : NDX/USD 1D  - RSI(2) < 10 + MA200, salida MA5
"""

import pandas as pd
import numpy as np
import yfinance as yf
import random

COST_RT = 0.0015
SPLIT   = 0.70
N_MC    = 5000   # TIS usa 5000 caminos

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

def metrics4(pnls, cost=COST_RT):
    if not pnls: return dict(fb=0,n=0,dd=100,fb_nb=0,pasa=0)
    fb = pf(pnls); n = len(pnls); dd = mdd(pnls)
    nb = sorted(pnls)[:-1] if n > 1 else pnls
    fb_nb = pf(nb)
    return dict(fb=fb, n=n, dd=dd, fb_nb=fb_nb,
                pasa=sum([fb>=1.3, n>=30, dd<20, fb_nb>1]))

def rsi_calc(s, p):
    d  = s.diff()
    u  = d.clip(lower=0).ewm(com=p-1, min_periods=p).mean()
    dn = (-d.clip(upper=0)).ewm(com=p-1, min_periods=p).mean()
    return 100 - 100 / (1 + u / dn)

def banner(t):
    print(f"\n{'#'*64}\n#  {t}\n{'#'*64}")

# ── datos ─────────────────────────────────────────────────────────────────────
def yf_get(ticker, start):
    raw = yf.download(ticker, start=start, end="2026-10-27",
                      interval="1d", progress=False, auto_adjust=True)
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = (raw[['Open','High','Low','Close']]
          .rename(columns={'Open':'open','High':'high','Low':'low','Close':'close'})
          .dropna().reset_index())
    df.columns = ['time','open','high','low','close']
    for c in ['open','high','low','close']:
        df[c] = df[c].astype(float)
    return df

print("Cargando datos...")
XAU = yf_get("GC=F",  "2000-01-01")
NDX = yf_get("^NDX",  "2000-01-01")
for name, df in [("XAU",XAU),("NDX",NDX)]:
    print(f"  {name}: {len(df)} barras  "
          f"{str(df['time'].iloc[0])[:10]} / {str(df['time'].iloc[-1])[:10]}")
SPL_XAU = int(len(XAU)*SPLIT)
SPL_NDX = int(len(NDX)*SPLIT)

# ── motores ───────────────────────────────────────────────────────────────────
def bt_pullback(df, n=7, ma=200, stop=0.02, cost=COST_RT, split_idx=None):
    df = df.copy().reset_index(drop=True)
    spl = split_idx if split_idx is not None else int(len(df)*SPLIT)
    df['ma'] = df['close'].rolling(ma).mean()
    trades, state = [], 'BUSCANDO'
    ep=ei=sp=None; pending=False
    for i in range(ma+n, len(df)):
        row=df.loc[i]; prev=df.loc[i-n:i-1]
        if pending:
            ep=row['open']; ei=i; sp=ep*(1-stop); state='DENTRO'; pending=False
        if state=='DENTRO':
            if row['low']<=sp:
                trades.append({'i':ei,'pnl':(sp-ep)/ep-cost,'oos':ei>=spl,
                               'time':str(df.loc[ei,'time'])})
                state='BUSCANDO'
            elif row['close']>prev['high'].max():
                trades.append({'i':ei,'pnl':(row['close']-ep)/ep-cost,'oos':ei>=spl,
                               'time':str(df.loc[ei,'time'])})
                state='BUSCANDO'
        if state=='BUSCANDO':
            if (not pd.isna(row['ma'])
                    and row['close']<prev['low'].min()
                    and row['close']>row['ma']):
                pending=True
    if state=='DENTRO':
        trades.append({'i':ei,'pnl':(df.iloc[-1]['close']-ep)/ep-cost,
                       'oos':ei>=spl,'time':str(df.loc[ei,'time'])})
    return trades

def bt_rsi2(df, rsi_lvl=10, ma_entry=200, ma_exit=5, cost=COST_RT, split_idx=None):
    df = df.copy().reset_index(drop=True)
    spl = split_idx if split_idx is not None else int(len(df)*SPLIT)
    df['ma200']=df['close'].rolling(ma_entry).mean()
    df['ma5']=df['close'].rolling(ma_exit).mean()
    df['rsi2']=rsi_calc(df['close'],2)
    trades,state=[],  'BUSCANDO'
    ep=ei=None; pi=pe=False
    for i in range(ma_entry+1,len(df)):
        row=df.loc[i]
        if pi and state=='BUSCANDO':
            ep=row['open']; ei=i; state='DENTRO'; pi=False
        if pe and state=='DENTRO':
            trades.append({'i':ei,'pnl':(row['open']-ep)/ep-cost,'oos':ei>=spl,
                           'time':str(df.loc[ei,'time'])})
            state='BUSCANDO'; pe=False
        if state=='DENTRO':
            if not pd.isna(row['ma5']) and row['close']>row['ma5']: pe=True
        if state=='BUSCANDO':
            if (not pd.isna(row['rsi2']) and not pd.isna(row['ma200'])
                    and row['rsi2']<rsi_lvl and row['close']>row['ma200']): pi=True
    if state=='DENTRO':
        trades.append({'i':ei,'pnl':(df.iloc[-1]['close']-ep)/ep-cost,
                       'oos':ei>=spl,'time':str(df.loc[ei,'time'])})
    return trades

# ── F1 ───────────────────────────────────────────────────────────────────────
def f1(trades, spl):
    oos = [t for t in trades if t['oos']]
    is_ = [t for t in trades if not t['oos']]
    m = metrics4([t['pnl'] for t in oos])
    ok = lambda v: "OK" if v else "XX"
    print(f"  IS trades: {len(is_)}  |  OOS trades: {m['n']}")
    print(f"  FB {m['fb']:.3f} {ok(m['fb']>=1.3)} | Ops {m['n']} {ok(m['n']>=30)} | "
          f"DD {m['dd']:.1f}% {ok(m['dd']<20)} | FB_nb {m['fb_nb']:.3f} {ok(m['fb_nb']>1)}")
    v = "APRUEBA" if m['pasa']==4 else "NO APRUEBA"
    print(f"  F1: {v}  ({m['pasa']}/4)")
    return v, [t['pnl'] for t in is_], [t['pnl'] for t in oos]

# ── F2 WALK-FORWARD (criterios TIS) ──────────────────────────────────────────
def f2_wf(df, bt_fn, bpy=252, is_y=3, oos_y=1):
    """
    Eficiencia = PF_OOS / PF_IS  (promedio de todas las ventanas)
    Anos en positivo >= 60%
    Peor caida en un ano (dentro del OOS) < 20%
    """
    is_b=int(is_y*bpy); oos_b=int(oos_y*bpy); win=is_b+oos_b
    wf_results=[]
    start=0
    while start+win<=len(df):
        seg=df.iloc[start:start+win].copy().reset_index(drop=True)
        all_t=bt_fn(seg, split_idx=is_b)
        is_p=[t['pnl'] for t in all_t if not t['oos']]
        oos_p=[t['pnl'] for t in all_t if t['oos']]
        pf_is=pf(is_p); pf_oos=pf(oos_p)
        efic=pf_oos/pf_is if pf_is>0 else 0.0
        d_ini=str(seg['time'].iloc[is_b])[:10]
        d_fin=str(seg['time'].iloc[-1])[:10]
        dd_oos=mdd(oos_p)
        wf_results.append({'per':f"{d_ini[:4]}",'pf_is':pf_is,'pf_oos':pf_oos,
                           'efic':efic,'pos':sum(oos_p)>0,'dd':dd_oos,'n':len(oos_p)})
        start+=oos_b

    print(f"  {'Ano':>6} {'PF IS':>7} {'PF OOS':>7} {'Efic':>6} {'Pos':>5} {'DD OOS':>7}")
    print(f"  {'-'*48}")
    n_pos=0; worst_dd=0.0; efic_list=[]
    for r in wf_results:
        tag="SI" if r['pos'] else "NO"
        n_pos+=int(r['pos'])
        worst_dd=max(worst_dd, r['dd'])
        if r['pf_is']>0: efic_list.append(r['efic'])
        print(f"  {r['per']:>6} {r['pf_is']:>7.3f} {r['pf_oos']:>7.3f} "
              f"{r['efic']:>6.2f} {tag:>5} {r['dd']:>6.1f}%")

    n=len(wf_results)
    pct_pos=n_pos/n*100 if n else 0
    efic_avg=sum(efic_list)/len(efic_list) if efic_list else 0

    print(f"\n  Eficiencia promedio : {efic_avg:.2f}  (umbral >=0.50)")
    print(f"  Anos positivos      : {n_pos}/{n} ({pct_pos:.0f}%)  (umbral >=60%)")
    print(f"  Peor caida en ano   : {worst_dd:.1f}%  (umbral <20%)")

    c1=efic_avg>=0.50; c2=pct_pos>=60; c3=worst_dd<20
    ok=lambda v: "OK" if v else "XX"
    print(f"  Criterios: efic {ok(c1)} | pos {ok(c2)} | DD {ok(c3)}")
    v="APRUEBA" if (c1 and c2 and c3) else "NO APRUEBA"
    print(f"  F2: {v}")
    return v

# ── F3 MESETA ─────────────────────────────────────────────────────────────────
def f3_meseta(df, base_pnl, grid, bt_fn_p, spl):
    """
    Peor vecino: max degradacion respecto al caso base
    Criterio TIS: peor vecino degrada < 30% (anti-precipicio)
    """
    base_fb=pf(base_pnl)
    print(f"  Caso base FB: {base_fb:.3f}")
    print(f"  {'Params':<30} {'FB':>7} {'Delta%':>8}  Pass")
    print(f"  {'-'*55}")
    worst_delta=0.0
    for p in grid:
        t=bt_fn_p(df,p,spl)
        oos=[x['pnl'] for x in t if x['oos']]
        fb_v=pf(oos)
        delta=((fb_v-base_fb)/base_fb*100) if base_fb>0 else -100
        worst_delta=min(worst_delta,delta)
        label=" ".join(f"{k}={v}" for k,v in p.items())
        m=metrics4(oos)
        print(f"  {label:<30} {fb_v:>7.3f} {delta:>+7.1f}%  {m['pasa']}/4")
    print(f"\n  Peor vecino: {worst_delta:+.1f}%  (umbral >-30%)")
    v="APRUEBA" if worst_delta>-30 else "NO APRUEBA"
    print(f"  F3: {v}")
    return v

# ── F4 MONTE CARLO (5000 caminos) ─────────────────────────────────────────────
def f4_mc(trades_oos, seed=42):
    """
    5000 reordenaciones aleatorias (bootstrap con reposicion)
    Criterio TIS: caida maxima peor 5% < 25%
    """
    random.seed(seed)
    n=len(trades_oos)
    if n==0: print("  Sin trades OOS."); return "NO APRUEBA"
    dd_list=[]
    for _ in range(N_MC):
        sample=random.choices(trades_oos,k=n)
        dd_list.append(mdd([t['pnl'] for t in sample]))
    dd_list.sort()
    p95=dd_list[int(0.95*N_MC)]   # peor 5%
    p50=dd_list[N_MC//2]
    pct_bajo25=sum(1 for d in dd_list if d<25)/N_MC*100
    print(f"  {N_MC} caminos bootstrap")
    print(f"  DD mediana         : {p50:.1f}%")
    print(f"  DD peor 5%         : {p95:.1f}%  (umbral <25%)")
    print(f"  Caminos con DD<25% : {pct_bajo25:.1f}%")
    v="APRUEBA" if p95<25 else "NO APRUEBA"
    print(f"  F4: {v}")
    return v

# ── F5 STRESS ─────────────────────────────────────────────────────────────────
def f5_stress(df, bt_fn, spl, base_oos_pnl):
    """
    Test 1: costes x2  ->  PF >= 1.10
    Test 2: sin las 2 mejores operaciones  ->  PF >= 1.10
    """
    # costes x2
    t2=bt_fn(df,cost=COST_RT*2,split_idx=spl)
    oos2=[x['pnl'] for x in t2 if x['oos']]
    pf2=pf(oos2)
    ok=lambda v: "OK" if v else "XX"
    print(f"  Costes x2:            PF {pf2:.3f}  {ok(pf2>=1.10)}  (umbral >=1.10)")

    # sin 2 mejores
    sorted_pnl=sorted(base_oos_pnl, reverse=True)
    sin2=sorted_pnl[2:] if len(sorted_pnl)>2 else []
    pf_sin2=pf(sin2)
    print(f"  Sin 2 mejores ops:    PF {pf_sin2:.3f}  {ok(pf_sin2>=1.10)}  (umbral >=1.10)")

    c1=pf2>=1.10; c2=pf_sin2>=1.10
    v="APRUEBA" if (c1 and c2) else "NO APRUEBA"
    print(f"  F5: {v}")
    return v

# ══════════════════════════════════════════════════════════════════════════════
# H3c — XAU
# ══════════════════════════════════════════════════════════════════════════════
banner("H3c · XAU/USD 1D · Pullback MA200, salida MAX7 (stop -2%)")

trades_xau=bt_pullback(XAU, split_idx=SPL_XAU)
oos_xau=[t for t in trades_xau if t['oos']]
is_xau =[t for t in trades_xau if not t['oos']]

print("\nF1 DISENO:")
v1x,is_pnl_x,oos_pnl_x=f1(trades_xau, SPL_XAU)

print("\nF2 WALK-FORWARD (IS=3a, OOS=1a):")
v2x=f2_wf(XAU, lambda df,split_idx=None: bt_pullback(df,split_idx=split_idx))

print("\nF3 MESETA (n_bars x MA_periodo):")
grid_xau=[{'n':n,'ma':m} for n in [5,6,7,8,9] for m in [150,175,200,225,250]]
def bx_p(df,p,spl): return bt_pullback(df,n=p['n'],ma=p['ma'],split_idx=spl)
v3x=f3_meseta(XAU, oos_pnl_x, grid_xau, bx_p, SPL_XAU)

print("\nF4 MONTE CARLO (5000 caminos):")
v4x=f4_mc(oos_xau)

print("\nF5 STRESS:")
v5x=f5_stress(XAU, bt_pullback, SPL_XAU, oos_pnl_x)

fx=[v1x,v2x,v3x,v4x,v5x]
np_x=sum(1 for f in fx if f=="APRUEBA")
print(f"\n{'='*64}")
print(f"RESUMEN H3c: F1 {v1x} | F2 {v2x} | F3 {v3x} | F4 {v4x} | F5 {v5x}")
print(f"PROTOCOLO : {np_x}/5  {'>>> APRUEBA <<<' if np_x>=4 else 'NO APRUEBA'}")

# ══════════════════════════════════════════════════════════════════════════════
# H3d — NDX
# ══════════════════════════════════════════════════════════════════════════════
banner("H3d · NDX/USD 1D · RSI(2)<10 + MA200, salida MA5")

trades_ndx=bt_rsi2(NDX, split_idx=SPL_NDX)
oos_ndx=[t for t in trades_ndx if t['oos']]

print("\nF1 DISENO:")
v1n,is_pnl_n,oos_pnl_n=f1(trades_ndx, SPL_NDX)

print("\nF2 WALK-FORWARD (IS=3a, OOS=1a):")
v2n=f2_wf(NDX, lambda df,split_idx=None: bt_rsi2(df,split_idx=split_idx))

print("\nF3 MESETA (RSI_nivel x MA_salida):")
grid_ndx=[{'rsi_lvl':r,'ma_exit':m} for r in [5,7,10,15,20] for m in [3,4,5,6,7]]
def bn_p(df,p,spl): return bt_rsi2(df,rsi_lvl=p['rsi_lvl'],ma_exit=p['ma_exit'],split_idx=spl)
v3n=f3_meseta(NDX, oos_pnl_n, grid_ndx, bn_p, SPL_NDX)

print("\nF4 MONTE CARLO (5000 caminos):")
v4n=f4_mc(oos_ndx)

print("\nF5 STRESS:")
v5n=f5_stress(NDX, bt_rsi2, SPL_NDX, oos_pnl_n)

fn=[v1n,v2n,v3n,v4n,v5n]
np_n=sum(1 for f in fn if f=="APRUEBA")
print(f"\n{'='*64}")
print(f"RESUMEN H3d: F1 {v1n} | F2 {v2n} | F3 {v3n} | F4 {v4n} | F5 {v5n}")
print(f"PROTOCOLO : {np_n}/5  {'>>> APRUEBA <<<' if np_n>=4 else 'NO APRUEBA'}")

print("\n\nFIN.")
