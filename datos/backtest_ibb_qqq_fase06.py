"""
IBB vs QQQ - Fase 06 Robustez: reducir DD del diseno (<20%)
Problema: diseno 2001-2019 tiene DD 40%+ por crashes 2002 y 2008
Soluciones a testear:
  A) Filtro SPY MA200 (si el mercado amplio cae, ir a cash)
  B) MA100 en vez de MA200 (reacciona mas rapido)
  C) Doble filtro: SPY MA200 + ETF ganador MA200
  D) Filtro SPY MA200 + momentum 60 dias
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf

COST  = 0.0015
SPLIT = 0.70

def load(fname):
    df = pd.read_csv(fname, parse_dates=['fecha'], index_col='fecha')
    df = df[['open','high','low','close','volume']].astype(float)
    df.sort_index(inplace=True)
    return df

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

# ── datos ────────────────────────────────────────────────────────────────────
ibb = load('ibb_1d_yahoo.csv')
qqq = load('qqq_1d_yahoo.csv')

# bajar SPY si no existe
import os
spy_file = 'spy_1d_yahoo.csv'
if not os.path.exists(spy_file):
    print('Bajando SPY...')
    spy_df = yf.download('SPY', start='2000-01-01', auto_adjust=True, progress=False)
    spy_df = spy_df[['Open','High','Low','Close','Volume']]
    spy_df.columns = ['open','high','low','close','volume']
    spy_df.index.name = 'fecha'
    spy_df.to_csv(spy_file)
    print(f'  SPY: {len(spy_df)} velas')
spy = load(spy_file)

joint = pd.DataFrame({
    'ibb': ibb['close'],
    'qqq': qqq['close'],
    'spy': spy['close'],
}).dropna()

# calcular indicadores para distintas configs
for sym in ['ibb', 'qqq', 'spy']:
    for lb in [20, 60]:
        joint[f'{sym}_ret{lb}'] = joint[sym].pct_change(lb)
    for ma in [100, 200]:
        joint[f'{sym}_ma{ma}'] = joint[sym].rolling(ma).mean()

joint['mes'] = joint.index.to_period('M')
joint = joint.dropna()
eom = pd.DatetimeIndex(
    joint.groupby('mes', group_keys=False).apply(lambda x: x.index[-1]).values
)

split_i = int(len(eom) * SPLIT)
split_t = eom[split_i]
print(f"Diseno: {eom[0].date()} a {eom[split_i-1].date()}")
print(f"Examen: {eom[split_i].date()} a {eom[-1].date()}")

def run(name, lb=20, etf_ma=200, spy_filter=False, spy_ma=200):
    trades = []
    holding = None

    for k in range(1, len(eom)):
        date      = eom[k]
        prev_date = eom[k-1]
        row       = joint.loc[date]

        ibb_ret = row[f'ibb_ret{lb}']
        qqq_ret = row[f'qqq_ret{lb}']
        winner  = 'ibb' if ibb_ret > qqq_ret else 'qqq'

        # filtro 1: SPY por encima de su MA (mercado amplio)
        if spy_filter:
            if row['spy'] < row[f'spy_ma{spy_ma}']:
                winner = 'cash'

        # filtro 2: ETF ganador por encima de su MA
        if winner != 'cash':
            if row[winner] < row[f'{winner}_ma{etf_ma}']:
                winner = 'cash'

        # calcular PNL del mes anterior
        if holding is not None and holding != 'cash':
            p_entry = joint.loc[prev_date, holding]
            p_exit  = joint.loc[date, holding]
            cambio  = (holding != winner)
            c       = COST if cambio else 0
            pnl     = (p_exit - p_entry) / p_entry - c
            trades.append({'pnl': pnl, 'entry_t': prev_date,
                           'exit_t': date, 'holding': holding,
                           'oos': prev_date >= split_t})
        elif holding == 'cash' and winner != 'cash':
            trades.append({'pnl': -COST/2, 'entry_t': prev_date,
                           'exit_t': date, 'holding': 'cash',
                           'oos': prev_date >= split_t})
        elif holding is not None and holding != 'cash' and winner == 'cash':
            p_entry = joint.loc[prev_date, holding]
            p_exit  = joint.loc[date, holding]
            pnl     = (p_exit - p_entry) / p_entry - COST
            trades.append({'pnl': pnl, 'entry_t': prev_date,
                           'exit_t': date, 'holding': holding,
                           'oos': prev_date >= split_t})

        holding = winner
    return trades

# ── variantes ────────────────────────────────────────────────────────────────
configs = [
    ('BASE · mom20 · ETF MA200',            dict(lb=20, etf_ma=200, spy_filter=False)),
    ('A   · SPY MA200 + ETF MA200 · mom20', dict(lb=20, etf_ma=200, spy_filter=True,  spy_ma=200)),
    ('B   · SPY MA200 + ETF MA100 · mom20', dict(lb=20, etf_ma=100, spy_filter=True,  spy_ma=200)),
    ('C   · SPY MA100 + ETF MA200 · mom20', dict(lb=20, etf_ma=200, spy_filter=True,  spy_ma=100)),
    ('D   · SPY MA200 + ETF MA200 · mom60', dict(lb=60, etf_ma=200, spy_filter=True,  spy_ma=200)),
    ('E   · SPY MA200 · sin ETF MA · mom20',dict(lb=20, etf_ma=200, spy_filter=True,  spy_ma=200)),
]

resultados = []
for nombre, kw in configs:
    trades = run(nombre, **kw)
    dis = [t['pnl'] for t in trades if not t['oos']]
    exa = [t['pnl'] for t in trades if t['oos']]
    print(f"\n{'='*58}")
    print(f"  {nombre}")
    print(f"  ops total={len(trades)}  dis={len(dis)}  exa={len(exa)}")
    print("  -- DISENO --")
    md = metrics(dis, 'dis')
    print("  -- EXAMEN --")
    me = metrics(exa, 'exa')
    resultados.append((nombre, trades, md, me))

# ── tabla resumen ─────────────────────────────────────────────────────────────
print(f"\n{'='*72}")
print(f"{'Variante':<42} {'DIS':>4}  {'PF':>6}  {'DD':>7}  {'EXA':>4}  {'PF':>6}  {'DD':>7}")
print(f"{'-'*72}")
for nombre, _, md, me in resultados:
    ds = f"{md['score']}/4" if md else ' -- '
    es = f"{me['score']}/4" if me else ' -- '
    dpf= f"{md['pf']:.3f}" if md else '  -- '
    epf= f"{me['pf']:.3f}" if me else '  -- '
    ddd= f"{md['dd']:.1f}%" if md else '  -- '
    edd= f"{me['dd']:.1f}%" if me else '  -- '
    tag = ' <-- APRUEBA DISENO' if md and md['score']==4 else ''
    print(f"  {nombre:<40} {ds}  {dpf}  {ddd}  {es}  {epf}  {edd}{tag}")

# ── curva de la mejor variante en diseno ─────────────────────────────────────
candidates = [(n,t,md,me) for n,t,md,me in resultados if md and md['score']==4]
if not candidates:
    candidates = sorted([(n,t,md,me) for n,t,md,me in resultados if md],
                         key=lambda x: (x[2]['score'], -x[2]['dd']), reverse=True)
best_n, best_t, best_md, best_me = candidates[0]
print(f"\nMejor en diseno: {best_n}")

all_t = sorted(best_t, key=lambda x: x['entry_t'])
eq_times = [joint.index[0]]
eq_vals  = [1.0]
eq = 1.0
for t in all_t:
    eq *= (1 + t['pnl'])
    eq_times.append(t['exit_t'])
    eq_vals.append(eq)
eq_s = pd.Series(eq_vals, index=eq_times)
bh   = joint['qqq'] / joint['qqq'].iloc[0]

fig, axes = plt.subplots(2, 1, figsize=(14,8), gridspec_kw={'height_ratios':[3,1]})
fig.suptitle(f'IBB vs QQQ Fase 06 · {best_n}', fontsize=10, fontweight='bold')
ax = axes[0]
ax.plot(eq_s.index, (eq_s-1)*100, color='#44dd88', lw=1.5, label='Estrategia')
ax.plot(bh.index,  (bh-1)*100,   color='#888',    lw=1, ls='--', label='QQQ B&H')
ax.axvline(split_t, color='#44aaff', lw=1, ls=':', label='Inicio examen')
ax.set_ylabel('Retorno (%)'); ax.legend(fontsize=9); ax.grid(alpha=0.2)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
eq_s2 = eq_s.reindex(eq_s.index.union(bh.index)).ffill()
dd_s  = (eq_s2 - eq_s2.cummax()) / eq_s2.cummax() * 100
axes[1].fill_between(dd_s.index, dd_s, 0, color='#cc4444', alpha=0.6)
axes[1].set_ylabel('Caida (%)'); axes[1].grid(alpha=0.2)
axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.tight_layout()
out = '../resultados/curva_ibb_qqq_fase06.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f'Grafico: {out}')
plt.show()
