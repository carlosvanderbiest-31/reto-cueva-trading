"""
MTUM como proxy de T20M
MTUM = iShares MSCI USA Momentum Factor ETF (desde 2013)
Rebalancea semestralmente por momentum ajustado por riesgo en acciones US grandes.
Prueba: RSI2 sobre MTUM y rotacion MTUM vs SPY como estrategias derivadas.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
import os

COST  = 0.0015
SPLIT = 0.70

def load_or_download(sym, fname, start='2013-01-01'):
    if not os.path.exists(fname):
        print(f'Bajando {sym}...')
        df = yf.download(sym, start=start, auto_adjust=True, progress=False)
        df = df[['Open','High','Low','Close','Volume']]
        df.columns = ['open','high','low','close','volume']
        df.index.name = 'fecha'
        df.to_csv(fname)
        print(f'  {fname}: {len(df)} velas  {df.index[0].date()} -> {df.index[-1].date()}')
    df = pd.read_csv(fname, parse_dates=['fecha'], index_col='fecha')
    return df[['open','high','low','close','volume']].astype(float).sort_index()

mtum = load_or_download('MTUM', 'mtum_1d_yahoo.csv', '2013-01-01')
spy  = load_or_download('SPY',  'spy_1d_yahoo.csv',  '2000-01-01')

print(f"\nMTUM: {len(mtum)} velas  {mtum.index[0].date()} a {mtum.index[-1].date()}")
print(f"SPY : {len(spy)}  velas  {spy.index[0].date()} a {spy.index[-1].date()}")

def rsi2(series):
    d = series.diff()
    g = d.clip(lower=0).rolling(2).mean()
    l = (-d.clip(upper=0)).rolling(2).mean()
    return 100 - 100 / (1 + g / l.replace(0, np.nan))

def metrics(pnls, label, verbose=True):
    if not pnls:
        print(f"  {label}: sin operaciones"); return None
    w    = sum(p for p in pnls if p > 0)
    l    = abs(sum(p for p in pnls if p <= 0))
    pf   = w / l if l else float('inf')
    n    = len(pnls)
    wins = sum(1 for p in pnls if p > 0)
    sp   = sorted(pnls)
    pf_nb = (sum(x for x in sp[:-1] if x>0) /
             abs(sum(x for x in sp[:-1] if x<=0))
             if any(x<=0 for x in sp[:-1]) else float('inf'))
    eq, pk, dd = 1.0, 1.0, 0.0
    for p in pnls:
        eq *= (1+p); pk = max(pk,eq); dd = max(dd,(pk-eq)/pk)
    ret = (eq-1)*100
    ok  = lambda c: 'OK' if c else '--'
    score = sum([pf>=1.3, n>=30, dd<0.20, pf_nb>1])
    if verbose:
        print(f"  PF         {pf:6.3f}  {ok(pf>=1.3)}")
        print(f"  Ops        {n:6d}  {ok(n>=30)}")
        print(f"  DD       {dd*100:6.1f}%  {ok(dd<0.20)}")
        print(f"  PF_nb      {pf_nb:6.3f}  {ok(pf_nb>1)}")
        print(f"  Acierto   {wins/n*100:5.1f}%")
        print(f"  Retorno   {ret:+.1f}%")
        print(f"  VEREDICTO {score}/4  {'APRUEBA' if score==4 else 'NO APRUEBA'}")
    return dict(pf=pf, n=n, dd=dd*100, pf_nb=pf_nb, score=score, ret=ret)

# ═══════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 1: RSI2 sobre MTUM (igual que RSI2 QQQ pero en MTUM)
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*58)
print("ESTRATEGIA 1: RSI2 MTUM (mismo sistema que RSI2 QQQ)")
print("="*58)

mtum['ma200'] = mtum['close'].rolling(200).mean()
mtum['ma5']   = mtum['close'].rolling(5).mean()
mtum['rsi']   = rsi2(mtum['close'])
mtum_clean    = mtum.dropna()

split_i1 = int(len(mtum_clean) * SPLIT)
split_t1  = mtum_clean.index[split_i1]

trades1 = []
in_pos  = False
entry_p = entry_i = None

for i in range(1, len(mtum_clean)):
    row  = mtum_clean.iloc[i]
    prev = mtum_clean.iloc[i-1]
    if in_pos:
        salida = None
        if row['close'] > row['ma5']:
            salida = ('ma5', row['close'])
        elif prev['rsi'] > 90:
            salida = ('rsi', row['open'])
        if salida:
            razon, ps = salida
            pnl = (ps - entry_p) / entry_p - COST
            trades1.append({'pnl': pnl, 'entry_t': mtum_clean.index[entry_i],
                            'exit_t': mtum_clean.index[i],
                            'oos': mtum_clean.index[entry_i] >= split_t1})
            in_pos = False
    if not in_pos and row['close'] > row['ma200'] and prev['rsi'] < 10:
        entry_p = row['open']
        entry_i = i
        in_pos  = True

dis1 = [t['pnl'] for t in trades1 if not t['oos']]
exa1 = [t['pnl'] for t in trades1 if t['oos']]
print(f"Total ops: {len(trades1)}  dis={len(dis1)}  exa={len(exa1)}")
print(f"Diseno: {mtum_clean.index[0].date()} a {mtum_clean.index[split_i1-1].date()}")
print(f"Examen: {mtum_clean.index[split_i1].date()} a {mtum_clean.index[-1].date()}")
print("\n-- DISENO --")
m1d = metrics(dis1, 'dis')
print("-- EXAMEN --")
m1e = metrics(exa1, 'exa')

# ═══════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 2: Rotacion MTUM vs SPY (cuando momentum es bueno, ir a MTUM)
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*58)
print("ESTRATEGIA 2: Rotacion mensual MTUM vs SPY por momentum")
print("="*58)

joint = pd.DataFrame({
    'mtum': mtum['close'],
    'spy':  spy['close'],
}).dropna()
joint['mtum_ret20'] = joint['mtum'].pct_change(20)
joint['spy_ret20']  = joint['spy'].pct_change(20)
joint['mtum_ma200'] = joint['mtum'].rolling(200).mean()
joint['spy_ma200']  = joint['spy'].rolling(200).mean()
joint['mes'] = joint.index.to_period('M')
joint = joint.dropna()
eom = pd.DatetimeIndex(
    joint.groupby('mes', group_keys=False).apply(lambda x: x.index[-1]).values
)

split_i2 = int(len(eom) * SPLIT)
split_t2  = eom[split_i2]

trades2 = []
holding = None
for k in range(1, len(eom)):
    date      = eom[k]
    prev_date = eom[k-1]
    row       = joint.loc[date]
    winner    = 'mtum' if row['mtum_ret20'] > row['spy_ret20'] else 'spy'
    if row[winner] < row[f'{winner}_ma200']:
        winner = 'cash'
    if holding is not None and holding != 'cash':
        p_entry = joint.loc[prev_date, holding]
        p_exit  = joint.loc[date, holding]
        cambio  = (holding != winner)
        c = COST if cambio else 0
        trades2.append({'pnl': (p_exit-p_entry)/p_entry - c,
                        'entry_t': prev_date, 'exit_t': date,
                        'oos': prev_date >= split_t2})
    elif holding == 'cash' and winner != 'cash':
        trades2.append({'pnl': -COST/2, 'entry_t': prev_date,
                        'exit_t': date, 'oos': prev_date >= split_t2})
    elif holding is not None and holding != 'cash' and winner == 'cash':
        p_entry = joint.loc[prev_date, holding]
        p_exit  = joint.loc[date, holding]
        trades2.append({'pnl': (p_exit-p_entry)/p_entry - COST,
                        'entry_t': prev_date, 'exit_t': date,
                        'oos': prev_date >= split_t2})
    holding = winner

dis2 = [t['pnl'] for t in trades2 if not t['oos']]
exa2 = [t['pnl'] for t in trades2 if t['oos']]
print(f"Total ops: {len(trades2)}  dis={len(dis2)}  exa={len(exa2)}")
print("\n-- DISENO --")
m2d = metrics(dis2, 'dis')
print("-- EXAMEN --")
m2e = metrics(exa2, 'exa')

# ── resumen y curvas ──────────────────────────────────────────────────────────
print(f"\n{'='*65}")
print("RESUMEN MTUM (proxy T20M)")
print(f"{'='*65}")
for nombre, md, me in [("RSI2 MTUM", m1d, m1e), ("MTUM vs SPY rotacion", m2d, m2e)]:
    ds = f"{md['score']}/4" if md else '--'
    es = f"{me['score']}/4" if me else '--'
    print(f"  {nombre:<25}  Diseno: {ds}  Examen: {es}")

fig, axes = plt.subplots(2, 1, figsize=(14, 8))
fig.suptitle('MTUM como proxy T20M — dos estrategias', fontsize=11, fontweight='bold')

for ax, (trades, ref_df, col, title, color, spt) in zip(axes, [
    (trades1, mtum_clean, 'close', 'RSI2 MTUM', '#f0c040', split_t1),
    (trades2, joint, 'mtum', 'Rotacion MTUM vs SPY', '#aa66ff', split_t2),
]):
    all_t = sorted(trades, key=lambda x: x['entry_t'])
    eq_times = [ref_df.index[0]]
    eq_vals  = [1.0]
    eq = 1.0
    for t in all_t:
        eq *= (1 + t['pnl'])
        eq_times.append(t['exit_t'])
        eq_vals.append(eq)
    eq_s = pd.Series(eq_vals, index=eq_times)
    bh   = ref_df[col] / ref_df[col].iloc[0]
    ax.plot(eq_s.index, (eq_s-1)*100, color=color, lw=1.5, label='Estrategia')
    ax.plot(bh.index,   (bh-1)*100,   color='#888', lw=1, ls='--', label='MTUM B&H')
    ax.axvline(spt, color='#44aaff', lw=1, ls=':', label='Inicio examen')
    ax.set_title(title, fontsize=10)
    ax.set_ylabel('Retorno (%)')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.tight_layout()
out = '../resultados/curva_mtum_proxy.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f'\nGrafico: {out}')
plt.show()
