"""
Mega Cueva Tester — Protocolo Completo (5 fases)
  H3c : XAU/USD 1D  — Pullback MA200, salida MAX7  (stop -2%)
  H3d : NDX/USD 1D  — RSI(2) < 10 + MA200, salida MA5

F1 Diseno      : ya aprobado 4/4
F2 Walk-Forward: ventanas IS=3a OOS=1a, paso 1a  —  umbral 60% positivas
F3 Meseta      : grilla de parametros vecinos  —  umbral 60% con FB>=1.0
F4 Monte Carlo : 1000 bootstrap  —  umbral 60% sims con FB>=1.3
F5 Stress      : costes x2 + ano mas flojo del OOS
"""

import pandas as pd
import numpy as np
import yfinance as yf
import random

COST_RT = 0.0015
SPLIT   = 0.70
N_MC    = 1000

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

def metrics4(pnls):
    if not pnls:
        return dict(fb=0, n=0, dd=100, fb_nb=0, pasa=0)
    fb = pf(pnls); n = len(pnls); dd = mdd(pnls)
    nb = sorted(pnls)[:-1] if n > 1 else pnls
    fb_nb = pf(nb)
    return dict(fb=fb, n=n, dd=dd, fb_nb=fb_nb,
                pasa=sum([fb>=1.3, n>=30, dd<20, fb_nb>1]))

def rsi_calc(s, p):
    d = s.diff()
    u  = d.clip(lower=0).ewm(com=p-1, min_periods=p).mean()
    dn = (-d.clip(upper=0)).ewm(com=p-1, min_periods=p).mean()
    return 100 - 100 / (1 + u / dn)

def banner(t):
    print(f"\n{'#'*62}\n#  {t}\n{'#'*62}")

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
XAU = yf_get("GC=F", "2000-01-01")
NDX = yf_get("^NDX", "2000-01-01")
for name, df in [("XAU", XAU), ("NDX", NDX)]:
    print(f"  {name}: {len(df)} barras  "
          f"{str(df['time'].iloc[0])[:10]} / {str(df['time'].iloc[-1])[:10]}")

SPL_XAU = int(len(XAU) * SPLIT)
SPL_NDX = int(len(NDX) * SPLIT)

# ── motores ───────────────────────────────────────────────────────────────────
def bt_pullback(df, n=7, ma=200, stop=0.02, cost=COST_RT, split_idx=None):
    df  = df.copy().reset_index(drop=True)
    spl = split_idx if split_idx is not None else int(len(df) * SPLIT)
    df['ma'] = df['close'].rolling(ma).mean()
    trades, state = [], 'BUSCANDO'
    ep = ei = sp = None; pending = False
    for i in range(ma + n, len(df)):
        row = df.loc[i]; prev = df.loc[i-n:i-1]
        if pending:
            ep=row['open']; ei=i; sp=ep*(1-stop); state='DENTRO'; pending=False
        if state == 'DENTRO':
            if row['low'] <= sp:
                trades.append({'i':ei,'pnl':(sp-ep)/ep-cost,'oos':ei>=spl,
                               'time':str(df.loc[ei,'time'])})
                state='BUSCANDO'
            elif row['close'] > prev['high'].max():
                trades.append({'i':ei,'pnl':(row['close']-ep)/ep-cost,'oos':ei>=spl,
                               'time':str(df.loc[ei,'time'])})
                state='BUSCANDO'
        if state == 'BUSCANDO':
            if (not pd.isna(row['ma'])
                    and row['close'] < prev['low'].min()
                    and row['close'] > row['ma']):
                pending = True
    if state == 'DENTRO':
        trades.append({'i':ei,'pnl':(df.iloc[-1]['close']-ep)/ep-cost,
                       'oos':ei>=spl,'time':str(df.loc[ei,'time'])})
    return trades

def bt_rsi2(df, rsi_lvl=10, ma_entry=200, ma_exit=5, cost=COST_RT, split_idx=None):
    df  = df.copy().reset_index(drop=True)
    spl = split_idx if split_idx is not None else int(len(df) * SPLIT)
    df['ma200'] = df['close'].rolling(ma_entry).mean()
    df['ma5']   = df['close'].rolling(ma_exit).mean()
    df['rsi2']  = rsi_calc(df['close'], 2)
    trades, state = [], 'BUSCANDO'
    ep = ei = None; pend_in = pend_ex = False
    for i in range(ma_entry + 1, len(df)):
        row = df.loc[i]
        if pend_in and state=='BUSCANDO':
            ep=row['open']; ei=i; state='DENTRO'; pend_in=False
        if pend_ex and state=='DENTRO':
            trades.append({'i':ei,'pnl':(row['open']-ep)/ep-cost,'oos':ei>=spl,
                           'time':str(df.loc[ei,'time'])})
            state='BUSCANDO'; pend_ex=False
        if state=='DENTRO':
            if not pd.isna(row['ma5']) and row['close'] > row['ma5']:
                pend_ex=True
        if state=='BUSCANDO':
            if (not pd.isna(row['rsi2']) and not pd.isna(row['ma200'])
                    and row['rsi2'] < rsi_lvl and row['close'] > row['ma200']):
                pend_in=True
    if state=='DENTRO':
        trades.append({'i':ei,'pnl':(df.iloc[-1]['close']-ep)/ep-cost,
                       'oos':ei>=spl,'time':str(df.loc[ei,'time'])})
    return trades

# ── F2: Walk-Forward ──────────────────────────────────────────────────────────
def f2_wf(df, bt_fn, bpy=252, is_y=3, oos_y=1):
    is_b = int(is_y * bpy); oos_b = int(oos_y * bpy); win = is_b + oos_b
    results = []
    start = 0
    while start + win <= len(df):
        seg   = df.iloc[start:start+win].copy().reset_index(drop=True)
        t_oos = [t for t in bt_fn(seg, split_idx=is_b) if t['oos']]
        pnls  = [t['pnl'] for t in t_oos]
        d_ini = str(seg['time'].iloc[is_b])[:10]
        d_fin = str(seg['time'].iloc[-1])[:10]
        results.append({'per': f"{d_ini}/{d_fin}", 'n': len(pnls),
                        'fb': pf(pnls), 'pos': sum(pnls) > 0 if pnls else False})
        start += oos_b

    print(f"  {'Periodo OOS':<26} {'Ops':>5} {'FB':>7}  Positivo")
    print(f"  {'-'*52}")
    n_pos = 0
    for r in results:
        tag = "SI" if r['pos'] else "NO"
        n_pos += int(r['pos'])
        print(f"  {r['per']:<26} {r['n']:>5} {r['fb']:>7.3f}  {tag}")
    pct = n_pos / len(results) * 100 if results else 0
    v = "APRUEBA" if pct >= 60 else "NO APRUEBA"
    print(f"\n  Positivas: {n_pos}/{len(results)} ({pct:.0f}%)  |  F2: {v}")
    return v

# ── F3: Meseta ────────────────────────────────────────────────────────────────
def f3_meseta(df, grid, bt_fn_p, spl):
    print(f"  {'Parametros':<28} {'FB':>6} {'N':>5} {'DD':>6}  Pass")
    print(f"  {'-'*52}")
    n_ok = 0
    for p in grid:
        t   = bt_fn_p(df, p, spl)
        oos = [x['pnl'] for x in t if x['oos']]
        m   = metrics4(oos)
        ok  = m['fb'] >= 1.0
        n_ok += int(ok)
        label = " ".join(f"{k}={v}" for k, v in p.items())
        print(f"  {label:<28} {m['fb']:>6.3f} {m['n']:>5} {m['dd']:>5.1f}%  "
              f"{m['pasa']}/4 {'*' if ok else ''}")
    pct = n_ok / len(grid) * 100
    v = "APRUEBA" if pct >= 60 else "NO APRUEBA"
    print(f"\n  Con FB>=1.0: {n_ok}/{len(grid)} ({pct:.0f}%)  |  F3: {v}")
    return v

# ── F4: Monte Carlo ───────────────────────────────────────────────────────────
def f4_mc(trades_oos, seed=42):
    random.seed(seed)
    n = len(trades_oos)
    if n == 0:
        print("  Sin trades OOS."); return "NO APRUEBA"
    fb_l, dd_l = [], []
    for _ in range(N_MC):
        s  = random.choices(trades_oos, k=n)
        pl = [t['pnl'] for t in s]
        fb_l.append(pf(pl)); dd_l.append(mdd(pl))
    pct_fb  = sum(1 for f in fb_l if f >= 1.3) / N_MC * 100
    pct_dd  = sum(1 for d in dd_l if d < 20)   / N_MC * 100
    med_fb  = sorted(fb_l)[N_MC // 2]
    p5_dd   = sorted(dd_l)[int(0.95 * N_MC)]
    v = "APRUEBA" if pct_fb >= 60 else "NO APRUEBA"
    print(f"  Sims FB>=1.3 : {pct_fb:5.1f}%  (umbral 60%)")
    print(f"  Sims DD<20%  : {pct_dd:5.1f}%")
    print(f"  FB mediana   : {med_fb:.3f}")
    print(f"  DD peor 5%%  : {p5_dd:.1f}%")
    print(f"  F4: {v}")
    return v

# ── F5: Stress ────────────────────────────────────────────────────────────────
def f5_stress(df, bt_fn, spl):
    # costes x2
    t2 = bt_fn(df, cost=COST_RT*2, split_idx=spl)
    oos2 = [x['pnl'] for x in t2 if x['oos']]
    m2   = metrics4(oos2)
    ok   = lambda v: "OK" if v else "XX"
    print(f"  Costes x2:  FB {m2['fb']:.3f} {ok(m2['fb']>=1.3)} | "
          f"DD {m2['dd']:.1f}% {ok(m2['dd']<20)} | {m2['pasa']}/4")

    # ano peor en OOS original
    t_oos = [x for x in bt_fn(df, split_idx=spl) if x['oos']]
    anos  = {}
    for t in t_oos:
        y = t.get('time','')[:4]
        if y: anos.setdefault(y, []).append(t['pnl'])

    worst_fb = 999; worst_y = ''
    if anos:
        print("  PnL por ano en OOS:")
        for y in sorted(anos):
            fb_y = pf(anos[y]); s = sum(anos[y])
            print(f"    {y}: {len(anos[y]):>3} ops  FB {fb_y:.3f}  pnl {s:+.4f}")
            if fb_y < worst_fb: worst_fb=fb_y; worst_y=y
        print(f"  Ano peor: {worst_y}  FB={worst_fb:.3f} "
              f"{ok(worst_fb>=1.0)} (umbral FB>=1.0)")

    ok_stress = m2['fb'] >= 1.3 and (worst_fb >= 1.0 or not anos)
    v = "APRUEBA" if ok_stress else "NO APRUEBA"
    print(f"  F5: {v}")
    return v

# ══════════════════════════════════════════════════════════════════════════════
# H3c — XAU
# ══════════════════════════════════════════════════════════════════════════════
banner("H3c · XAU/USD 1D · Pullback MA200, salida MAX7 (stop -2%)")

print("\nF1 DISENO:  4/4  APRUEBA  (ya verificado)")

print("\nF2 WALK-FORWARD:")
wf_xau = f2_wf(XAU, lambda df, split_idx=None: bt_pullback(df, split_idx=split_idx))

print("\nF3 MESETA (n_bars x MA_periodo):")
grid_xau = [{'n':n,'ma':m} for n in [5,6,7,8,9] for m in [150,175,200,225,250]]
def bt_xau_p(df, p, spl): return bt_pullback(df, n=p['n'], ma=p['ma'], split_idx=spl)
ms_xau = f3_meseta(XAU, grid_xau, bt_xau_p, SPL_XAU)

print("\nF4 MONTE CARLO:")
mc_xau = f4_mc([t for t in bt_pullback(XAU, split_idx=SPL_XAU) if t['oos']])

print("\nF5 STRESS:")
st_xau = f5_stress(XAU, bt_pullback, SPL_XAU)

fx = [wf_xau, ms_xau, mc_xau, st_xau]
np_x = 1 + sum(1 for f in fx if f=="APRUEBA")
print(f"\n{'='*62}")
print(f"RESUMEN H3c: F1 APRUEBA | F2 {wf_xau} | F3 {ms_xau} | F4 {mc_xau} | F5 {st_xau}")
print(f"PROTOCOLO : {np_x}/5  {'>>> APRUEBA <<<' if np_x >= 4 else 'NO APRUEBA'}")

# ══════════════════════════════════════════════════════════════════════════════
# H3d — NDX
# ══════════════════════════════════════════════════════════════════════════════
banner("H3d · NDX/USD 1D · RSI(2)<10 + MA200, salida MA5")

print("\nF1 DISENO:  4/4  APRUEBA  (ya verificado)")

print("\nF2 WALK-FORWARD:")
wf_ndx = f2_wf(NDX, lambda df, split_idx=None: bt_rsi2(df, split_idx=split_idx))

print("\nF3 MESETA (RSI_nivel x MA_salida):")
grid_ndx = [{'rsi_lvl':r,'ma_exit':m} for r in [5,7,10,15,20] for m in [3,4,5,6,7]]
def bt_ndx_p(df, p, spl): return bt_rsi2(df, rsi_lvl=p['rsi_lvl'], ma_exit=p['ma_exit'], split_idx=spl)
ms_ndx = f3_meseta(NDX, grid_ndx, bt_ndx_p, SPL_NDX)

print("\nF4 MONTE CARLO:")
mc_ndx = f4_mc([t for t in bt_rsi2(NDX, split_idx=SPL_NDX) if t['oos']])

print("\nF5 STRESS:")
st_ndx = f5_stress(NDX, bt_rsi2, SPL_NDX)

fn = [wf_ndx, ms_ndx, mc_ndx, st_ndx]
np_n = 1 + sum(1 for f in fn if f=="APRUEBA")
print(f"\n{'='*62}")
print(f"RESUMEN H3d: F1 APRUEBA | F2 {wf_ndx} | F3 {ms_ndx} | F4 {mc_ndx} | F5 {st_ndx}")
print(f"PROTOCOLO : {np_n}/5  {'>>> APRUEBA <<<' if np_n >= 4 else 'NO APRUEBA'}")

print("\n\nFIN.")
