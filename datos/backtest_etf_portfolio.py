"""
Backtest de 3 estrategias del portafolio de Mariel:
  1. RSI2 QQQ  : RSI(2) mean-reversion en QQQ (proxy NDX)
  2. IBB_QQQ   : Rotacion mensual IBB vs QQQ por momentum
  3. IBB_IBIT  : Rotacion mensual IBB vs IBIT por momentum
Coste : 0.15% roundtrip
Split : 70/30
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

COST  = 0.0015
SPLIT = 0.70

# ── helpers ─────────────────────────────────────────────────────────────────
def load(fname):
    df = pd.read_csv(fname, parse_dates=['fecha'], index_col='fecha')
    df = df[['open','high','low','close','volume']].astype(float)
    df.sort_index(inplace=True)
    return df

def rsi2(series):
    delta = series.diff()
    g = delta.clip(lower=0).rolling(2).mean()
    l = (-delta.clip(upper=0)).rolling(2).mean()
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
        print(f"  PF         {pf:6.3f}  {ok(pf>=1.3)}  (>=1.30)")
        print(f"  Ops        {n:6d}  {ok(n>=30)}  (>=30)")
        print(f"  DD       {dd*100:6.1f}%  {ok(dd<0.20)}  (<20%)")
        print(f"  PF_nb      {pf_nb:6.3f}  {ok(pf_nb>1)}  (>1)")
        print(f"  Acierto   {wins/n*100:5.1f}%")
        print(f"  Retorno   {ret:+.1f}%")
        print(f"  VEREDICTO {score}/4  {'APRUEBA' if score==4 else 'NO APRUEBA'}")
    return dict(pf=pf, n=n, dd=dd*100, pf_nb=pf_nb, score=score, ret=ret)

# ═══════════════════════════════════════════════════════════════════════════
# 1. RSI2 QQQ
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("ESTRATEGIA 1: RSI2 QQQ (Larry Connors adaptado)")
print("="*60)
print("Reglas: precio > MA200 + RSI(2) < 10  => COMPRA")
print("        RSI(2) > 90 O cierre > MA5    => VENDE")

qqq = load('qqq_1d_yahoo.csv')
qqq['ma200'] = qqq['close'].rolling(200).mean()
qqq['ma5']   = qqq['close'].rolling(5).mean()
qqq['rsi']   = rsi2(qqq['close'])
qqq = qqq.dropna()

split_i = int(len(qqq) * SPLIT)
split_t = qqq.index[split_i]

trades_rsi2 = []
in_pos = False
entry_p = entry_i = None

for i in range(1, len(qqq)):
    row  = qqq.iloc[i]
    prev = qqq.iloc[i-1]

    if in_pos:
        salida = None
        if row['close'] > row['ma5']:
            salida = ('ma5', row['close'])
        elif prev['rsi'] > 90:
            salida = ('rsi_exit', row['open'])

        if salida:
            razon, psalida = salida
            pnl = (psalida - entry_p) / entry_p - COST
            trades_rsi2.append({'pnl': pnl, 'entry_i': entry_i,
                                 'exit_t': qqq.index[i], 'entry_t': qqq.index[entry_i],
                                 'oos': qqq.index[entry_i] >= split_t})
            in_pos = False

    if not in_pos and row['close'] > row['ma200'] and prev['rsi'] < 10:
        entry_p = row['open']
        entry_i = i
        in_pos  = True

dis1 = [t['pnl'] for t in trades_rsi2 if not t['oos']]
exa1 = [t['pnl'] for t in trades_rsi2 if t['oos']]
print(f"\nTotal ops: {len(trades_rsi2)} (dis={len(dis1)}, exa={len(exa1)})")
print(f"Periodo diseno : {qqq.index[0].date()} a {qqq.index[split_i-1].date()}")
print(f"Periodo examen : {qqq.index[split_i].date()} a {qqq.index[-1].date()}")
print("\n-- DISENO --")
m_rsi2_dis = metrics(dis1, 'diseno')
print("-- EXAMEN --")
m_rsi2_exa = metrics(exa1, 'examen')

# ═══════════════════════════════════════════════════════════════════════════
# 2. IBB vs QQQ — rotacion mensual por momentum 20 dias
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("ESTRATEGIA 2: IBB vs QQQ (rotacion mensual momentum)")
print("="*60)
print("Reglas: fin de mes, compara retorno 20d de IBB vs QQQ")
print("        Mantener el que tuvo mayor retorno. Cambio = coste.")

ibb = load('ibb_1d_yahoo.csv')
qqq2 = load('qqq_1d_yahoo.csv')

# alinear fechas
joint = pd.DataFrame({
    'ibb': ibb['close'],
    'qqq': qqq2['close'],
}).dropna()

joint['ibb_ret20'] = joint['ibb'].pct_change(20)
joint['qqq_ret20'] = joint['qqq'].pct_change(20)
joint['mes'] = joint.index.to_period('M')

# fin de cada mes
eom = joint.groupby('mes').apply(lambda x: x.index[-1]).values

split_i2 = int(len(eom) * SPLIT)
split_t2 = eom[split_i2]

trades_rot1 = []
holding = None
prev_eom_idx = None

for k, date in enumerate(eom):
    row = joint.loc[date]
    if pd.isna(row['ibb_ret20']) or pd.isna(row['qqq_ret20']):
        continue
    winner = 'ibb' if row['ibb_ret20'] > row['qqq_ret20'] else 'qqq'

    if prev_eom_idx is not None and holding is not None:
        # calcular retorno del mes que acaba de terminar
        prev_date = eom[k-1]
        p_entry = joint.loc[prev_date, holding]
        p_exit  = joint.loc[date, holding]
        cambio  = (holding != winner)
        c       = COST if cambio else 0
        pnl     = (p_exit - p_entry) / p_entry - c
        trades_rot1.append({
            'entry_t': prev_date, 'exit_t': date,
            'holding': holding, 'pnl': pnl,
            'oos': prev_date >= split_t2
        })
    holding = winner
    prev_eom_idx = k

dis2 = [t['pnl'] for t in trades_rot1 if not t['oos']]
exa2 = [t['pnl'] for t in trades_rot1 if t['oos']]
print(f"\nTotal ops: {len(trades_rot1)} (dis={len(dis2)}, exa={len(exa2)})")
print("\n-- DISENO --")
m_rot1_dis = metrics(dis2, 'diseno')
print("-- EXAMEN --")
m_rot1_exa = metrics(exa2, 'examen')

# ═══════════════════════════════════════════════════════════════════════════
# 3. IBB vs IBIT — rotacion mensual por momentum
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("ESTRATEGIA 3: IBB vs IBIT (rotacion mensual momentum)")
print("="*60)
print("Reglas: fin de mes, compara retorno 20d de IBB vs IBIT")
print("        Solo disponible desde ene-2024 (IBIT lanzado)")

ibit = load('ibit_1d_yahoo.csv')
joint2 = pd.DataFrame({
    'ibb':  ibb['close'],
    'ibit': ibit['close'],
}).dropna()

joint2['ibb_ret20']  = joint2['ibb'].pct_change(20)
joint2['ibit_ret20'] = joint2['ibit'].pct_change(20)
joint2['mes'] = joint2.index.to_period('M')
eom2 = joint2.groupby('mes').apply(lambda x: x.index[-1]).values

split_i3 = int(len(eom2) * SPLIT)
split_t3  = eom2[split_i3] if split_i3 < len(eom2) else eom2[-1]

trades_rot2 = []
holding2 = None

for k, date in enumerate(eom2):
    row = joint2.loc[date]
    if pd.isna(row['ibb_ret20']) or pd.isna(row['ibit_ret20']):
        continue
    winner = 'ibb' if row['ibb_ret20'] > row['ibit_ret20'] else 'ibit'
    if k > 0 and holding2 is not None:
        prev_date = eom2[k-1]
        p_entry = joint2.loc[prev_date, holding2]
        p_exit  = joint2.loc[date, holding2]
        cambio  = (holding2 != winner)
        c       = COST if cambio else 0
        pnl     = (p_exit - p_entry) / p_entry - c
        trades_rot2.append({
            'entry_t': prev_date, 'exit_t': date,
            'holding': holding2, 'pnl': pnl,
            'oos': prev_date >= split_t3
        })
    holding2 = winner

dis3 = [t['pnl'] for t in trades_rot2 if not t['oos']]
exa3 = [t['pnl'] for t in trades_rot2 if t['oos']]
print(f"\nTotal ops: {len(trades_rot2)} (dis={len(dis3)}, exa={len(exa3)})")
print(f"(IBIT solo tiene {len(joint2)} dias desde {joint2.index[0].date()})")
print("\n-- DISENO --")
m_rot2_dis = metrics(dis3, 'diseno')
print("-- EXAMEN --")
m_rot2_exa = metrics(exa3, 'examen')

# ── tabla resumen final ──────────────────────────────────────────────────────
print("\n" + "="*70)
print("RESUMEN FINAL — DISENO (in-sample)")
print("="*70)
for nombre, m in [("RSI2 QQQ", m_rsi2_dis), ("IBB vs QQQ rot.", m_rot1_dis), ("IBB vs IBIT rot.", m_rot2_dis)]:
    if m:
        ok = 'APRUEBA' if m['score']==4 else f"{m['score']}/4"
        print(f"  {nombre:<20} PF={m['pf']:.3f}  Ops={m['n']}  DD={m['dd']:.1f}%  PFnb={m['pf_nb']:.3f}  [{ok}]")

print("\nRESUMEN FINAL — EXAMEN (out-of-sample)")
print("="*70)
for nombre, m in [("RSI2 QQQ", m_rsi2_exa), ("IBB vs QQQ rot.", m_rot1_exa), ("IBB vs IBIT rot.", m_rot2_exa)]:
    if m:
        ok = 'APRUEBA' if m['score']==4 else f"{m['score']}/4"
        print(f"  {nombre:<20} PF={m['pf']:.3f}  Ops={m['n']}  DD={m['dd']:.1f}%  PFnb={m['pf_nb']:.3f}  [{ok}]")

# ── curvas de capital ────────────────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(14, 12))
fig.suptitle('Portafolio Mariel — 3 estrategias ETF', fontsize=13, fontweight='bold')

configs = [
    (trades_rsi2, qqq, 'RSI2 QQQ', split_t, '#f0c040'),
    (trades_rot1, joint, 'IBB vs QQQ rotacion', split_t2, '#44dd88'),
    (trades_rot2, joint2, 'IBB vs IBIT rotacion', split_t3, '#ff7744'),
]

for ax, (trades, ref, title, spt, color) in zip(axes, configs):
    all_t = sorted(trades, key=lambda x: x['entry_t'])
    eq_times = [ref.index[0]]
    eq_vals  = [1.0]
    eq = 1.0
    for t in all_t:
        eq *= (1 + t['pnl'])
        eq_times.append(t['exit_t'])
        eq_vals.append(eq)
    eq_s = pd.Series(eq_vals, index=eq_times)
    ax.plot(eq_s.index, (eq_s-1)*100, color=color, lw=1.5, label='Estrategia')
    ax.axvline(spt, color='#44aaff', lw=1, ls=':', label='Inicio examen')
    ax.set_title(title, fontsize=10)
    ax.set_ylabel('Retorno (%)')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.tight_layout()
out = '../resultados/curva_etf_portfolio.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f'\nGrafico guardado en {out}')
plt.show()
