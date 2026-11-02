"""
Backtest IBS < 0.1 sobre datos TradingView (BTC/USDT 4H)
Regla:
  ENTRA  : IBS < 0.10  (cierra en el 10% inferior de su rango)
  SALE   : cierre > high de la vela anterior
  TIEMPO : 5 velas máximo
  COSTE  : 0.15% roundtrip
  SPLIT  : 70% diseño / 30% examen  (misma lógica que el tester)
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

CSV    = 'btcusdt_4h_tradingview.csv'
COST   = 0.0015
SPLIT  = 0.70
MAX_V  = 5       # tope de tiempo en velas

# ── carga ──────────────────────────────────────────────────────────────────
df = pd.read_csv(CSV, parse_dates=['time'])
df.sort_values('time', inplace=True)
df.reset_index(drop=True, inplace=True)
for c in ['open','high','low','close']:
    df[c] = df[c].astype(float)

df['ibs'] = (df['close'] - df['low']) / (df['high'] - df['low'])

split_i = int(len(df) * SPLIT)
print(f"Total velas : {len(df)}")
print(f"Diseño      : {df.loc[0,'time'].date()} → {df.loc[split_i-1,'time'].date()}  ({split_i} velas)")
print(f"Examen      : {df.loc[split_i,'time'].date()} → {df.loc[len(df)-1,'time'].date()}  ({len(df)-split_i} velas)\n")

# ── backtest ────────────────────────────────────────────────────────────────
trades = []
in_pos = False
entry_p = entry_i = velas_dentro = None

for i in range(1, len(df)):
    row  = df.loc[i]
    prev = df.loc[i-1]

    if in_pos:
        velas_dentro += 1
        salida = None

        # a. señal: cierre > high de la vela anterior
        if row['close'] > prev['high']:
            salida = ('señal', row['close'])
        # b. tiempo: 5 velas
        elif velas_dentro >= MAX_V:
            salida = ('tiempo', row['close'])

        if salida:
            razon, precio_salida = salida
            pnl = (precio_salida - entry_p) / entry_p - COST
            trades.append({
                'entry_i': entry_i,
                'exit_i':  i,
                'entry_t': df.loc[entry_i, 'time'],
                'exit_t':  row['time'],
                'entry_p': entry_p,
                'exit_p':  precio_salida,
                'pnl':     pnl,
                'razon':   razon,
                'oos':     entry_i >= split_i,
                'velas':   velas_dentro,
            })
            in_pos = False

    if not in_pos and row['ibs'] < 0.10:
        entry_p = row['close']
        entry_i = i
        velas_dentro = 0
        in_pos = True

if in_pos:
    last = df.iloc[-1]
    pnl = (last['close'] - entry_p) / entry_p - COST
    trades.append({'entry_i': entry_i, 'exit_i': len(df)-1,
                   'entry_t': df.loc[entry_i,'time'], 'exit_t': last['time'],
                   'entry_p': entry_p, 'exit_p': last['close'],
                   'pnl': pnl, 'razon': 'fin', 'oos': entry_i >= split_i, 'velas': velas_dentro})

# ── métricas ────────────────────────────────────────────────────────────────
def metrics(pnls, label):
    if not pnls:
        print(f"{label}: sin operaciones"); return
    w   = sum(p for p in pnls if p > 0)
    l   = abs(sum(p for p in pnls if p <= 0))
    pf  = w/l if l else float('inf')
    n   = len(pnls)
    wins = sum(1 for p in pnls if p > 0)
    pf_nb = (lambda p2: sum(x for x in p2 if x>0)/abs(sum(x for x in p2 if x<=0)) if any(x<=0 for x in p2) else float('inf'))(sorted(pnls)[:-1])
    eq, pk, dd = 1.0, 1.0, 0.0
    for p in pnls:
        eq *= (1+p); pk = max(pk,eq); dd = max(dd,(pk-eq)/pk)
    ret = (eq-1)*100
    chk = lambda ok: '✓' if ok else '✗'
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    print(f"  PF              {pf:6.3f}  {chk(pf>=1.3)}  (≥ 1,30)")
    print(f"  Operaciones     {n:6d}  {chk(n>=30)}  (≥ 30)")
    print(f"  Caída máx.    {dd*100:6.1f}%  {chk(dd<0.20)}  (< 20%)")
    print(f"  PF sin mejor    {pf_nb:6.3f}  {chk(pf_nb>1)}  (> 1)")
    print(f"  Acierto       {wins/n*100:5.1f}%")
    print(f"  Retorno       {ret:+.1f}%")
    score = sum([pf>=1.3, n>=30, dd<0.20, pf_nb>1])
    print(f"  VEREDICTO     {score}/4  {'APRUEBA' if score==4 else 'NO APRUEBA'}")
    return pnls, eq

dis = [t['pnl'] for t in trades if not t['oos']]
exa = [t['pnl'] for t in trades if t['oos']]
metrics(dis, 'DISEÑO (in-sample)')
metrics(exa, 'EXAMEN (out-of-sample)')

# ── curva de capital ────────────────────────────────────────────────────────
all_trades = sorted(trades, key=lambda x: x['entry_i'])

eq_times  = [df.loc[0, 'time']]
eq_vals   = [1.0]
eq        = 1.0

for t in all_trades:
    eq *= (1 + t['pnl'])
    eq_times.append(t['exit_t'])
    eq_vals.append(eq)

eq_series = pd.Series(eq_vals, index=eq_times)

# buy & hold
bh = df.set_index('time')['close']
bh = bh / bh.iloc[0]

# ── plot ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(14, 8),
                          gridspec_kw={'height_ratios': [3, 1]})
fig.suptitle('IBS < 0.10 · BTC/USDT 4H · Datos TradingView', fontsize=13, fontweight='bold')

ax = axes[0]
ax.plot(eq_series.index, (eq_series - 1) * 100, color='#f0c040', lw=1.5, label='Estrategia (con costes)')
ax.plot(bh.index, (bh - 1) * 100, color='#888', lw=1, ls='--', label='Comprar y mantener')
split_t = df.loc[split_i, 'time']
ax.axvline(split_t, color='#44aaff', lw=1.2, ls=':', label='Inicio examen')
ax.set_ylabel('Retorno acumulado (%)')
ax.legend(fontsize=9)
ax.grid(alpha=0.2)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# drawdown
eq_s2   = eq_series.reindex(eq_series.index.union(bh.index)).ffill()
rolling_max = eq_s2.cummax()
dd_series   = (eq_s2 - rolling_max) / rolling_max * 100

ax2 = axes[1]
ax2.fill_between(dd_series.index, dd_series, 0, color='#cc4444', alpha=0.6)
ax2.set_ylabel('Caída desde máx. (%)')
ax2.set_ylim(dd_series.min() * 1.1, 5)
ax2.grid(alpha=0.2)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.tight_layout()
plt.savefig('../resultados/curva_ibs_tradingview.png', dpi=150, bbox_inches='tight')
print('\nGráfico guardado en resultados/curva_ibs_tradingview.png')
plt.show()
