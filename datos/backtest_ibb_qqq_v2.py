"""
IBB vs QQQ rotacion mensual v2 — con filtro de efectivo (cash filter)
Si el activo ganador por momentum esta por debajo de su MA200, se va a cash.
Coste : 0.15% roundtrip solo cuando hay cambio de posicion
Split : 70/30
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
        print(f"  PF         {pf:6.3f}  {ok(pf>=1.3)}  (>=1.30)")
        print(f"  Ops        {n:6d}  {ok(n>=30)}  (>=30)")
        print(f"  DD       {dd*100:6.1f}%  {ok(dd<0.20)}  (<20%)")
        print(f"  PF_nb      {pf_nb:6.3f}  {ok(pf_nb>1)}  (>1)")
        print(f"  Acierto   {wins/n*100:5.1f}%")
        print(f"  Retorno   {ret:+.1f}%")
        print(f"  VEREDICTO {score}/4  {'APRUEBA' if score==4 else 'NO APRUEBA'}")
    return dict(pf=pf, n=n, dd=dd*100, pf_nb=pf_nb, score=score, ret=ret, wins=wins/n*100)

ibb = load('ibb_1d_yahoo.csv')
qqq = load('qqq_1d_yahoo.csv')

joint = pd.DataFrame({
    'ibb': ibb['close'],
    'qqq': qqq['close'],
}).dropna()

# momentum 20d y MA200
for sym in ['ibb', 'qqq']:
    joint[f'{sym}_ret20'] = joint[sym].pct_change(20)
    joint[f'{sym}_ma200'] = joint[sym].rolling(200).mean()

joint['mes'] = joint.index.to_period('M')
joint = joint.dropna()

eom = joint.groupby('mes', group_keys=False).apply(lambda x: x.index[-1]).values

split_i = int(len(eom) * SPLIT)
split_t = eom[split_i]

print(f"Total meses : {len(eom)}")
eom = pd.DatetimeIndex(eom)
print(f"Diseno      : {eom[0].date()} a {eom[split_i-1].date()}")
print(f"Examen      : {eom[split_i].date()} a {eom[-1].date()}")

def run_rotation(name, lookback=20, use_cash_filter=True):
    trades = []
    holding = None   # 'ibb', 'qqq', o 'cash'

    for k in range(1, len(eom)):
        date      = eom[k]
        prev_date = eom[k-1]
        row       = joint.loc[date]

        col_ret = f'_ret{lookback}'
        ibb_ret = joint.loc[date, f'ibb_ret{lookback}']
        qqq_ret = joint.loc[date, f'qqq_ret{lookback}']

        # decidir ganador por momentum
        winner = 'ibb' if ibb_ret > qqq_ret else 'qqq'

        # filtro de efectivo: si el ganador esta bajo su MA200 → cash
        if use_cash_filter:
            ma200_winner = joint.loc[date, f'{winner}_ma200']
            price_winner = joint.loc[date, winner]
            if price_winner < ma200_winner:
                winner = 'cash'

        # calcular retorno del mes anterior
        if holding is not None and holding != 'cash':
            p_entry = joint.loc[prev_date, holding]
            p_exit  = joint.loc[date, holding]
            cambio  = (holding != winner)
            c       = COST if cambio else 0
            pnl     = (p_exit - p_entry) / p_entry - c
            trades.append({
                'entry_t': prev_date, 'exit_t': date,
                'holding': holding, 'next': winner,
                'pnl': pnl,
                'oos': prev_date >= split_t
            })
        elif holding == 'cash' and holding != winner and winner != 'cash':
            # salio de cash, no hay retorno del periodo en cash (0% - coste entrada)
            trades.append({
                'entry_t': prev_date, 'exit_t': date,
                'holding': 'cash', 'next': winner,
                'pnl': -COST / 2,  # solo coste de entrada
                'oos': prev_date >= split_t
            })
        elif holding is not None and holding != 'cash' and winner == 'cash':
            # entra a cash: liquida la posicion
            p_entry = joint.loc[prev_date, holding]
            p_exit  = joint.loc[date, holding]
            pnl     = (p_exit - p_entry) / p_entry - COST
            trades.append({
                'entry_t': prev_date, 'exit_t': date,
                'holding': holding, 'next': 'cash',
                'pnl': pnl,
                'oos': prev_date >= split_t
            })

        holding = winner

    return trades

# ── test de variantes ────────────────────────────────────────────────────────
variantes = [
    ('IBB vs QQQ · mom20 · SIN filtro cash',  20, False),
    ('IBB vs QQQ · mom20 · CON filtro cash',  20, True),
    ('IBB vs QQQ · mom60 · CON filtro cash',  60, True),
    ('IBB vs QQQ · mom3m · CON filtro cash', 63, True),
]

resultados = []
for nombre, lb, cash in variantes:
    # recalcular lookback si hace falta
    joint[f'ibb_ret{lb}'] = joint['ibb'].pct_change(lb)
    joint[f'qqq_ret{lb}'] = joint['qqq'].pct_change(lb)

    trades = run_rotation(nombre, lb, cash)
    dis = [t['pnl'] for t in trades if not t['oos']]
    exa = [t['pnl'] for t in trades if t['oos']]

    print(f"\n{'='*60}")
    print(f"  {nombre}")
    print(f"  Total ops: {len(trades)}  (dis={len(dis)}, exa={len(exa)})")
    print("  -- DISENO --")
    md = metrics(dis, 'dis')
    print("  -- EXAMEN --")
    me = metrics(exa, 'exa')
    resultados.append((nombre, trades, md, me))

# ── tabla resumen ────────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("RESUMEN — DISENO")
print(f"{'='*70}")
for nombre, _, md, _ in resultados:
    if md:
        tag = 'APRUEBA' if md['score']==4 else f"{md['score']}/4"
        print(f"  {nombre[:45]:<45} PF={md['pf']:.3f}  DD={md['dd']:.1f}%  [{tag}]")

print(f"\n{'='*70}")
print("RESUMEN — EXAMEN")
print(f"{'='*70}")
for nombre, _, _, me in resultados:
    if me:
        tag = 'APRUEBA' if me['score']==4 else f"{me['score']}/4"
        print(f"  {nombre[:45]:<45} PF={me['pf']:.3f}  DD={me['dd']:.1f}%  [{tag}]")

# ── curva del mejor ──────────────────────────────────────────────────────────
best = max((r for r in resultados if r[2]), key=lambda x: (x[2]['score'], x[2]['pf']))
nombre_b, trades_b, md_b, me_b = best

all_t = sorted(trades_b, key=lambda x: x['entry_t'])
eq_times = [joint.index[0]]
eq_vals  = [1.0]
eq = 1.0
for t in all_t:
    eq *= (1 + t['pnl'])
    eq_times.append(t['exit_t'])
    eq_vals.append(eq)

eq_s = pd.Series(eq_vals, index=eq_times)

fig, axes = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [3,1]})
fig.suptitle(f'IBB vs QQQ Rotacion · {nombre_b}', fontsize=11, fontweight='bold')

ax = axes[0]
ax.plot(eq_s.index, (eq_s-1)*100, color='#44dd88', lw=1.5, label='Estrategia')
bh = joint['qqq'] / joint['qqq'].iloc[0]
ax.plot(bh.index, (bh-1)*100, color='#888', lw=1, ls='--', label='QQQ B&H')
ax.axvline(split_t, color='#44aaff', lw=1, ls=':', label='Inicio examen')
ax.set_ylabel('Retorno (%)')
ax.legend(fontsize=9)
ax.grid(alpha=0.2)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

eq_s2 = eq_s.reindex(eq_s.index.union(bh.index)).ffill()
pk    = eq_s2.cummax()
dd_s  = (eq_s2 - pk) / pk * 100

ax2 = axes[1]
ax2.fill_between(dd_s.index, dd_s, 0, color='#cc4444', alpha=0.6)
ax2.set_ylabel('Caida (%)')
ax2.set_ylim(dd_s.min()*1.1, 5)
ax2.grid(alpha=0.2)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.tight_layout()
out = '../resultados/curva_ibb_qqq_v2.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f'\nGrafico: {out}')
plt.show()
