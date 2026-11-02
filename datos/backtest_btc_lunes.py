"""
Backtest: BTC Efecto Lunes
Testa múltiples variantes del "Monday Effect" en BTC diario.
Datos   : btcusdt_1d_binance.csv
Coste   : 0.15% roundtrip (COST_RT = 0.0015)
Split   : 70% diseño / 30% examen
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

CSV    = 'btcusdt_1d_binance.csv'
COST   = 0.0015
SPLIT  = 0.70

# ── carga ──────────────────────────────────────────────────────────────────
df = pd.read_csv(CSV, parse_dates=['fecha'])
df.sort_values('fecha', inplace=True)
df.reset_index(drop=True, inplace=True)
for c in ['open','high','low','close']:
    df[c] = df[c].astype(float)

df['dow']    = df['fecha'].dt.dayofweek   # 0=lun, 4=vie
df['ibs']    = (df['close'] - df['low']) / (df['high'] - df['low'])
df['ma200']  = df['close'].rolling(200).mean()
df['rsi']    = None  # se calcula abajo

# RSI 14
delta = df['close'].diff()
gain  = delta.clip(lower=0).rolling(14).mean()
loss  = (-delta.clip(upper=0)).rolling(14).mean()
df['rsi14'] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))

split_i = int(len(df) * SPLIT)
print(f"Total días : {len(df)}")
print(f"Diseno     : {df.loc[0,'fecha'].date()} a {df.loc[split_i-1,'fecha'].date()}")
print(f"Examen     : {df.loc[split_i,'fecha'].date()} a {df.loc[len(df)-1,'fecha'].date()}")

# ── motor de backtest ───────────────────────────────────────────────────────
def backtest(name, entry_filter_fn, max_dias=5, exit_mode='señal'):
    """
    entry_filter_fn: función que recibe (df, i) → bool
    exit_mode:
      'señal'  → sale cuando cierre > high de vela anterior
      'viernes'→ sale en el cierre del viernes
      'mixto'  → lo primero de: señal ó viernes ó tiempo
    """
    trades = []
    in_pos = False
    entry_p = entry_i = dias_dentro = None

    for i in range(200, len(df)):
        row  = df.loc[i]
        prev = df.loc[i-1]

        if in_pos:
            dias_dentro += 1
            salida = None

            if exit_mode == 'señal':
                if row['close'] > prev['high']:
                    salida = ('señal', row['close'])
                elif dias_dentro >= max_dias:
                    salida = ('tiempo', row['close'])

            elif exit_mode == 'viernes':
                if row['dow'] == 4:                    # viernes
                    salida = ('viernes', row['close'])
                elif dias_dentro >= max_dias:
                    salida = ('tiempo', row['close'])

            elif exit_mode == 'mixto':
                if row['close'] > prev['high']:
                    salida = ('señal', row['close'])
                elif row['dow'] == 4:
                    salida = ('viernes', row['close'])
                elif dias_dentro >= max_dias:
                    salida = ('tiempo', row['close'])

            if salida:
                razon, psalida = salida
                pnl = (psalida - entry_p) / entry_p - COST
                trades.append({
                    'entry_i': entry_i,
                    'exit_i':  i,
                    'entry_t': df.loc[entry_i,'fecha'],
                    'exit_t':  row['fecha'],
                    'entry_p': entry_p,
                    'exit_p':  psalida,
                    'pnl':     pnl,
                    'razon':   razon,
                    'oos':     entry_i >= split_i,
                })
                in_pos = False

        # entrada: solo lunes + filtro
        if not in_pos and row['dow'] == 0 and entry_filter_fn(df, i):
            entry_p     = row['close']
            entry_i     = i
            dias_dentro = 0
            in_pos      = True

    return trades

# ── métricas ────────────────────────────────────────────────────────────────
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
        eq *= (1+p); pk = max(pk, eq); dd = max(dd, (pk-eq)/pk)
    ret = (eq - 1) * 100
    ok  = lambda c: '✓' if c else '✗'
    score = sum([pf>=1.3, n>=30, dd<0.20, pf_nb>1])
    if verbose:
        print(f"  PF           {pf:6.3f}  {ok(pf>=1.3)}")
        print(f"  Ops          {n:6d}  {ok(n>=30)}")
        print(f"  DD           {dd*100:5.1f}%  {ok(dd<0.20)}")
        print(f"  PF_nb        {pf_nb:6.3f}  {ok(pf_nb>1)}")
        print(f"  Acierto      {wins/n*100:5.1f}%")
        print(f"  Retorno      {ret:+.1f}%")
        print(f"  VEREDICTO    {score}/4  {'APRUEBA' if score==4 else 'NO APRUEBA'}")
    return dict(pf=pf, n=n, dd=dd*100, pf_nb=pf_nb, score=score, ret=ret, wins=wins/n*100)

def run(name, entry_fn, max_dias=5, exit_mode='mixto'):
    trades = backtest(name, entry_fn, max_dias, exit_mode)
    dis = [t['pnl'] for t in trades if not t['oos']]
    exa = [t['pnl'] for t in trades if t['oos']]
    print(f"\n{'='*55}")
    print(f"  {name}  [{exit_mode}, máx {max_dias} días]")
    print(f"  Total ops: {len(trades)} (dis={len(dis)}, exa={len(exa)})")
    print(f"{'='*55}")
    print("  ── DISEÑO ──")
    m_dis = metrics(dis, 'diseño')
    print("  ── EXAMEN ──")
    m_exa = metrics(exa, 'examen')
    return trades, m_dis, m_exa

# ── variantes a testear ─────────────────────────────────────────────────────
#  A) Todo lunes (sin filtro) → hasta viernes
#  B) Lunes + IBS < 0.5 (cerró en mitad baja del rango) → señal o viernes
#  C) Lunes + cierre < MA200 daily → señal o viernes
#  D) Lunes + RSI14 < 50 → señal o viernes
#  E) Lunes + IBS < 0.3 (cierre muy bajo en el rango) → señal o viernes
#  F) Lunes + precio < close del viernes anterior → buy the dip semanal

results = {}

results['A_sin_filtro'] = run(
    'A · Todo lunes sin filtro',
    lambda df, i: True,
    max_dias=5, exit_mode='mixto'
)

results['B_ibs05'] = run(
    'B · Lunes + IBS < 0.50',
    lambda df, i: df.loc[i, 'ibs'] < 0.50,
    max_dias=5, exit_mode='mixto'
)

results['C_ibs03'] = run(
    'C · Lunes + IBS < 0.30',
    lambda df, i: df.loc[i, 'ibs'] < 0.30,
    max_dias=5, exit_mode='mixto'
)

results['D_ibs01'] = run(
    'D · Lunes + IBS < 0.10',
    lambda df, i: df.loc[i, 'ibs'] < 0.10,
    max_dias=5, exit_mode='mixto'
)

results['E_ma200'] = run(
    'E · Lunes + precio > MA200 (solo bull)',
    lambda df, i: df.loc[i, 'close'] > df.loc[i, 'ma200'],
    max_dias=5, exit_mode='mixto'
)

results['F_dip_semanal'] = run(
    'F · Lunes + cierre < cierre viernes anterior',
    lambda df, i: (df.loc[i, 'close'] < df.loc[i-3, 'close']
                   if i >= 3 else False),
    max_dias=5, exit_mode='mixto'
)

results['G_rsi50'] = run(
    'G · Lunes + RSI14 < 50',
    lambda df, i: df.loc[i, 'rsi14'] < 50,
    max_dias=5, exit_mode='mixto'
)

results['H_ibs03_ma200'] = run(
    'H · Lunes + IBS < 0.30 + precio > MA200',
    lambda df, i: (df.loc[i, 'ibs'] < 0.30
                   and df.loc[i, 'close'] > df.loc[i, 'ma200']),
    max_dias=5, exit_mode='mixto'
)

# ── tabla resumen ────────────────────────────────────────────────────────────
print(f"\n{'='*75}")
print(f"TABLA RESUMEN — DISEÑO (in-sample)")
print(f"{'='*75}")
print(f"{'Variante':<40} {'PF':>6} {'Ops':>5} {'DD':>7} {'PFnb':>6} {'Score':>6}")
print(f"{'-'*75}")
for key, (trades, m_dis, m_exa) in results.items():
    if m_dis:
        m = m_dis
        ok = '[4/4]' if m['score']==4 else ('[3/4]' if m['score']==3 else '')
        name = key[:38]
        print(f"  {name:<38} {m['pf']:>6.3f} {m['n']:>5} {m['dd']:>6.1f}% {m['pf_nb']:>6.3f} {m['score']}/4 {ok}")

print(f"\n{'='*75}")
print(f"TABLA RESUMEN — EXAMEN (out-of-sample)")
print(f"{'='*75}")
print(f"{'Variante':<40} {'PF':>6} {'Ops':>5} {'DD':>7} {'PFnb':>6} {'Score':>6}")
print(f"{'-'*75}")
for key, (trades, m_dis, m_exa) in results.items():
    if m_exa:
        m = m_exa
        ok = '[4/4]' if m['score']==4 else ('[3/4]' if m['score']==3 else '')
        name = key[:38]
        print(f"  {name:<38} {m['pf']:>6.3f} {m['n']:>5} {m['dd']:>6.1f}% {m['pf_nb']:>6.3f} {m['score']}/4 {ok}")

# ── curva de la mejor variante ───────────────────────────────────────────────
# Encuentra la de mayor score en diseño, luego mayor PF
best_key = max(
    ((k, v) for k, v in results.items() if v[1]),
    key=lambda x: (x[1][1]['score'], x[1][1]['pf'])
)[0]
best_trades, best_dis_m, best_exa_m = results[best_key]

print(f"\n▶ MEJOR VARIANTE: {best_key}")

all_t = sorted(best_trades, key=lambda x: x['entry_i'])
eq_times = [df.loc[0,'fecha']]
eq_vals  = [1.0]
eq = 1.0
for t in all_t:
    eq *= (1 + t['pnl'])
    eq_times.append(t['exit_t'])
    eq_vals.append(eq)

eq_s = pd.Series(eq_vals, index=eq_times)
bh   = df.set_index('fecha')['close'] / df['close'].iloc[0]
split_t = df.loc[split_i, 'fecha']

fig, axes = plt.subplots(2, 1, figsize=(14, 8),
                          gridspec_kw={'height_ratios': [3, 1]})
fig.suptitle(f'BTC Efecto Lunes · {best_key} · Datos Binance diario', fontsize=12, fontweight='bold')

ax = axes[0]
ax.plot(eq_s.index, (eq_s - 1)*100, color='#f0c040', lw=1.5, label='Estrategia')
ax.plot(bh.index, (bh - 1)*100, color='#888', lw=1, ls='--', label='Buy & Hold')
ax.axvline(split_t, color='#44aaff', lw=1.2, ls=':', label='Inicio examen')
ax.set_ylabel('Retorno acumulado (%)')
ax.legend(fontsize=9)
ax.grid(alpha=0.2)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

eq_s2 = eq_s.reindex(eq_s.index.union(bh.index)).ffill()
pk    = eq_s2.cummax()
dd_s  = (eq_s2 - pk) / pk * 100

ax2 = axes[1]
ax2.fill_between(dd_s.index, dd_s, 0, color='#cc4444', alpha=0.6)
ax2.set_ylabel('Caída desde máx. (%)')
ax2.set_ylim(dd_s.min()*1.1, 5)
ax2.grid(alpha=0.2)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.tight_layout()
out = '../resultados/curva_btc_lunes.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f'\nGráfico guardado en {out}')
plt.show()
