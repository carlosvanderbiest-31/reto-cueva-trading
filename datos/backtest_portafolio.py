"""
Portafolio de 4 estrategias validadas 4/4
  1. EWMAC BTC 4H + MA200 diaria + stop 3%
  2. RSI2 QQQ   (mean-reversion Nasdaq 100)
  3. IBB vs QQQ + SPY MA200 + ETF MA100 (rotacion sectorial)
  4. RSI2 MTUM  (mean-reversion momentum ETF)

Periodo comun: 2014-01 a 2026-10 (MTUM arranca abr-2013 + 200d calentamiento)
Split        : 70/30 -> diseno hasta ~2023, examen desde ~2023
Pesos        : igual (25% c/u) y risk-parity (1/vol mensual)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
warnings.filterwarnings('ignore')

COST  = 0.0015
SPLIT = 0.70

# ═══════════════════════════════════════════════════════════════════════════
# helpers
# ═══════════════════════════════════════════════════════════════════════════
def load_csv(path, date_col='fecha'):
    df = pd.read_csv(path, parse_dates=[date_col], index_col=date_col)
    for c in ['open','high','low','close']:
        if c in df.columns:
            df[c] = df[c].astype(float)
    return df.sort_index()

def rsi2(series):
    d = series.diff()
    g = d.clip(lower=0).rolling(2).mean()
    l = (-d.clip(upper=0)).rolling(2).mean()
    return 100 - 100 / (1 + g / l.replace(0, np.nan))

def trades_to_monthly(trades, start, end):
    """Convierte lista de trades (con entry_t, exit_t, pnl) a retornos mensuales."""
    idx = pd.date_range(start, end, freq='ME')
    monthly_ret = pd.Series(0.0, index=idx)
    for t in trades:
        et = pd.Timestamp(t['entry_t'])
        xt = pd.Timestamp(t['exit_t'])
        pnl = t['pnl']
        months = pd.date_range(et, xt, freq='ME')
        if len(months) == 0:
            m = idx[idx >= xt]
            if len(m): monthly_ret[m[0]] += pnl
        else:
            # distribuir proporcionalmente por duracion en cada mes
            total_days = max((xt - et).days, 1)
            for m in months:
                m_start = m.replace(day=1)
                m_end   = m
                overlap = (min(xt, m_end) - max(et, m_start)).days
                frac    = max(overlap, 0) / total_days
                if m in monthly_ret.index:
                    monthly_ret[m] += pnl * frac
    return monthly_ret

def metrics_monthly(rets, label, verbose=True):
    if rets is None or len(rets.dropna()) == 0:
        print(f"  {label}: sin datos"); return None
    r = rets.dropna()
    w    = r[r > 0].sum()
    l    = abs(r[r <= 0].sum())
    pf   = w / l if l else float('inf')
    n    = len(r)
    wins = (r > 0).sum()
    rs   = r.sort_values()
    pf_nb = (rs.iloc[:-1][rs.iloc[:-1]>0].sum() /
             abs(rs.iloc[:-1][rs.iloc[:-1]<=0].sum())
             if (rs.iloc[:-1] <= 0).any() else float('inf'))
    eq   = (1 + r).cumprod()
    pk   = eq.cummax()
    dd   = ((eq - pk) / pk).min()
    ret  = (eq.iloc[-1] - 1) * 100
    ok   = lambda c: 'OK' if c else '--'
    score = sum([pf>=1.3, n>=30, abs(dd)<0.20, pf_nb>1])
    if verbose:
        print(f"  PF         {pf:6.3f}  {ok(pf>=1.3)}")
        print(f"  Meses      {n:6d}  {ok(n>=30)}")
        print(f"  DD       {dd*100:6.1f}%  {ok(abs(dd)<0.20)}")
        print(f"  PF_nb      {pf_nb:6.3f}  {ok(pf_nb>1)}")
        print(f"  Acierto   {wins/n*100:5.1f}%")
        print(f"  Retorno   {ret:+.1f}%")
        print(f"  SCORE     {score}/4  {'APRUEBA' if score==4 else 'NO APRUEBA'}")
    return dict(pf=pf, n=n, dd=abs(dd)*100, pf_nb=pf_nb, score=score, ret=ret,
                eq=eq, wins=wins/n*100)

# ═══════════════════════════════════════════════════════════════════════════
# periodo comun y split
# ═══════════════════════════════════════════════════════════════════════════
COMMON_START = pd.Timestamp('2014-02-01')
COMMON_END   = pd.Timestamp('2026-10-31')
all_months   = pd.date_range(COMMON_START, COMMON_END, freq='ME')
split_t      = all_months[int(len(all_months) * SPLIT)]
print(f"Periodo : {COMMON_START.date()} a {COMMON_END.date()}")
print(f"Diseno  : hasta {split_t.date()}")
print(f"Examen  : desde {(split_t + pd.offsets.MonthBegin()).date()}")

# ═══════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 1 · EWMAC BTC 4H + MA200 diaria + stop 3%
# ═══════════════════════════════════════════════════════════════════════════
print("\n[1/4] EWMAC BTC 4H...")
btc4h  = load_csv('BTCUSDT_4h.csv', date_col='timestamp') if 'timestamp' in pd.read_csv('BTCUSDT_4h.csv', nrows=0).columns else load_csv('BTCUSDT_4h.csv', date_col=pd.read_csv('BTCUSDT_4h.csv', nrows=0).columns[0])
# detectar nombre de columna de fecha
_cols = pd.read_csv('BTCUSDT_4h.csv', nrows=0).columns.tolist()
_date_col = _cols[0]
btc4h = pd.read_csv('BTCUSDT_4h.csv', parse_dates=[_date_col])
btc4h = btc4h.rename(columns={_date_col: 'fecha'})
btc4h.set_index('fecha', inplace=True)
for c in ['open','high','low','close']:
    btc4h[c] = btc4h[c].astype(float)
btc4h.index = btc4h.index.tz_localize(None) if btc4h.index.tz is not None else btc4h.index
btc4h.sort_index(inplace=True)

# MA200 diaria sobre cierre diario
btc1d = load_csv('btcusdt_1d_binance.csv')
btc1d['ma200'] = btc1d['close'].rolling(200).mean()

# EMA 8/32 en 4H
btc4h['ema8']  = btc4h['close'].ewm(span=8,  adjust=False).mean()
btc4h['ema32'] = btc4h['close'].ewm(span=32, adjust=False).mean()

trades_btc = []
in_pos = False
entry_p = stop = None

for i in range(1, len(btc4h)):
    row  = btc4h.iloc[i]
    prev = btc4h.iloc[i-1]
    ts = row.name
    if hasattr(ts, 'tz_localize') and ts.tz is not None:
        ts = ts.tz_localize(None)
    date_day = ts.normalize()

    # obtener MA200 diaria para ese dia
    ma200_row = btc1d['ma200'].asof(date_day)
    btc_daily_close = btc1d['close'].asof(date_day)
    above_ma200 = (btc_daily_close > ma200_row) if not pd.isna(ma200_row) else False

    if in_pos:
        # stop hit
        if row['low'] <= stop:
            pnl = (stop - entry_p) / entry_p - COST
            trades_btc.append({'entry_t': entry_t, 'exit_t': row.name, 'pnl': pnl})
            in_pos = False
        # senal de salida: EMA8 cruza abajo EMA32
        elif prev['ema8'] > prev['ema32'] and row['ema8'] <= row['ema32']:
            pnl = (row['close'] - entry_p) / entry_p - COST
            trades_btc.append({'entry_t': entry_t, 'exit_t': row.name, 'pnl': pnl})
            in_pos = False

    if not in_pos and above_ma200:
        # senal de entrada: EMA8 cruza arriba EMA32
        if prev['ema8'] <= prev['ema32'] and row['ema8'] > row['ema32']:
            entry_p = row['close']
            entry_t = row.name
            stop    = entry_p * 0.97
            in_pos  = True

print(f"  {len(trades_btc)} trades BTC EWMAC")
btc_monthly = trades_to_monthly(trades_btc, COMMON_START, COMMON_END)

# ═══════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 2 · RSI2 QQQ
# ═══════════════════════════════════════════════════════════════════════════
print("[2/4] RSI2 QQQ...")
qqq = load_csv('qqq_1d_yahoo.csv')
qqq['ma200'] = qqq['close'].rolling(200).mean()
qqq['ma5']   = qqq['close'].rolling(5).mean()
qqq['rsi']   = rsi2(qqq['close'])
qqq = qqq.dropna()

trades_qqq = []
in_pos = False; entry_p = entry_i = None
for i in range(1, len(qqq)):
    row  = qqq.iloc[i]
    prev = qqq.iloc[i-1]
    if in_pos:
        salida = None
        if row['close'] > row['ma5']:    salida = row['close']
        elif prev['rsi'] > 90:           salida = row['open']
        if salida:
            trades_qqq.append({'entry_t': qqq.index[entry_i], 'exit_t': qqq.index[i],
                                'pnl': (salida - entry_p) / entry_p - COST})
            in_pos = False
    if not in_pos and row['close'] > row['ma200'] and prev['rsi'] < 10:
        entry_p = row['open']; entry_i = i; in_pos = True

print(f"  {len(trades_qqq)} trades RSI2 QQQ")
qqq_monthly = trades_to_monthly(trades_qqq, COMMON_START, COMMON_END)

# ═══════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 3 · IBB vs QQQ + SPY MA200 + ETF MA100
# ═══════════════════════════════════════════════════════════════════════════
print("[3/4] IBB vs QQQ rotacion...")
ibb = load_csv('ibb_1d_yahoo.csv')
qqq2 = load_csv('qqq_1d_yahoo.csv')
spy  = load_csv('spy_1d_yahoo.csv')

joint = pd.DataFrame({'ibb': ibb['close'], 'qqq': qqq2['close'], 'spy': spy['close']}).dropna()
joint['ibb_ret20']  = joint['ibb'].pct_change(20)
joint['qqq_ret20']  = joint['qqq'].pct_change(20)
joint['ibb_ma100']  = joint['ibb'].rolling(100).mean()
joint['qqq_ma100']  = joint['qqq'].rolling(100).mean()
joint['spy_ma200']  = joint['spy'].rolling(200).mean()
joint['mes'] = joint.index.to_period('M')
joint = joint.dropna()
eom_rot = pd.DatetimeIndex(
    joint.groupby('mes', group_keys=False).apply(lambda x: x.index[-1]).values)

trades_rot = []
holding_rot = None
for k in range(1, len(eom_rot)):
    date = eom_rot[k]; prev_date = eom_rot[k-1]
    row  = joint.loc[date]
    winner = 'ibb' if row['ibb_ret20'] > row['qqq_ret20'] else 'qqq'
    if row['spy'] < row['spy_ma200']:                     winner = 'cash'
    elif row[winner] < row[f'{winner}_ma100']:            winner = 'cash'
    if holding_rot is not None and holding_rot != 'cash':
        c = COST if holding_rot != winner else 0
        pnl = (joint.loc[date, holding_rot] - joint.loc[prev_date, holding_rot]) / joint.loc[prev_date, holding_rot] - c
        trades_rot.append({'entry_t': prev_date, 'exit_t': date, 'pnl': pnl})
    elif holding_rot == 'cash' and winner != 'cash':
        trades_rot.append({'entry_t': prev_date, 'exit_t': date, 'pnl': -COST/2})
    elif holding_rot is not None and holding_rot != 'cash' and winner == 'cash':
        pnl = (joint.loc[date, holding_rot] - joint.loc[prev_date, holding_rot]) / joint.loc[prev_date, holding_rot] - COST
        trades_rot.append({'entry_t': prev_date, 'exit_t': date, 'pnl': pnl})
    holding_rot = winner

print(f"  {len(trades_rot)} meses IBB/QQQ")
rot_monthly = trades_to_monthly(trades_rot, COMMON_START, COMMON_END)

# ═══════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 4 · RSI2 MTUM
# ═══════════════════════════════════════════════════════════════════════════
print("[4/4] RSI2 MTUM...")
mtum = load_csv('mtum_1d_yahoo.csv')
mtum['ma200'] = mtum['close'].rolling(200).mean()
mtum['ma5']   = mtum['close'].rolling(5).mean()
mtum['rsi']   = rsi2(mtum['close'])
mtum = mtum.dropna()

trades_mtum = []
in_pos = False; entry_p = entry_i = None
for i in range(1, len(mtum)):
    row  = mtum.iloc[i]
    prev = mtum.iloc[i-1]
    if in_pos:
        salida = None
        if row['close'] > row['ma5']:   salida = row['close']
        elif prev['rsi'] > 90:          salida = row['open']
        if salida:
            trades_mtum.append({'entry_t': mtum.index[entry_i], 'exit_t': mtum.index[i],
                                 'pnl': (salida - entry_p) / entry_p - COST})
            in_pos = False
    if not in_pos and row['close'] > row['ma200'] and prev['rsi'] < 10:
        entry_p = row['open']; entry_i = i; in_pos = True

print(f"  {len(trades_mtum)} trades RSI2 MTUM")
mtum_monthly = trades_to_monthly(trades_mtum, COMMON_START, COMMON_END)

# ═══════════════════════════════════════════════════════════════════════════
# COMBINAR EN PORTAFOLIO
# ═══════════════════════════════════════════════════════════════════════════
strats = pd.DataFrame({
    'BTC_EWMAC': btc_monthly,
    'RSI2_QQQ':  qqq_monthly,
    'IBB_QQQ':   rot_monthly,
    'RSI2_MTUM': mtum_monthly,
}, index=all_months).fillna(0)

# ── peso igual ───────────────────────────────────────────────────────────────
port_eq = strats.mean(axis=1)   # 25% cada una

# ── risk parity (1/vol rolling 12m) ─────────────────────────────────────────
vol12 = strats.rolling(12).std().shift(1).replace(0, np.nan)
inv_vol = 1 / vol12
weights_rp = inv_vol.div(inv_vol.sum(axis=1), axis=0).fillna(0.25)
port_rp = (strats * weights_rp).sum(axis=1)

# ═══════════════════════════════════════════════════════════════════════════
# METRICAS
# ═══════════════════════════════════════════════════════════════════════════
def split_ret(r):
    dis = r[r.index <= split_t]
    exa = r[r.index >  split_t]
    return dis, exa

print(f"\n{'='*58}")
print("ESTRATEGIAS INDIVIDUALES (periodo comun, mensual)")
print(f"{'='*58}")
ind_results = {}
for name, series in strats.items():
    dis, exa = split_ret(series)
    print(f"\n-- {name} --")
    print("  Diseno:")
    md = metrics_monthly(dis, name)
    print("  Examen:")
    me = metrics_monthly(exa, name)
    ind_results[name] = (md, me)

print(f"\n{'='*58}")
print("PORTAFOLIO PESO IGUAL (25% cada estrategia)")
print(f"{'='*58}")
dis_eq, exa_eq = split_ret(port_eq)
print("\n  Diseno:")
md_eq = metrics_monthly(dis_eq, 'port_eq')
print("  Examen:")
me_eq = metrics_monthly(exa_eq, 'port_eq')

print(f"\n{'='*58}")
print("PORTAFOLIO RISK PARITY (1/vol rolling 12m)")
print(f"{'='*58}")
dis_rp, exa_rp = split_ret(port_rp)
print("\n  Diseno:")
md_rp = metrics_monthly(dis_rp, 'port_rp')
print("  Examen:")
me_rp = metrics_monthly(exa_rp, 'port_rp')

# ── tabla resumen ─────────────────────────────────────────────────────────────
print(f"\n{'='*72}")
print(f"{'Estrategia':<22} {'DIS':>4} {'PF':>6} {'DD':>7} {'Ret':>8}  {'EXA':>4} {'PF':>6} {'DD':>7} {'Ret':>8}")
print(f"{'-'*72}")
for name, (md, me) in ind_results.items():
    ds = f"{md['score']}/4" if md else '--'
    es = f"{me['score']}/4" if me else '--'
    print(f"  {name:<20} {ds} {md['pf']:6.3f} {md['dd']:6.1f}% {md['ret']:+7.1f}%  "
          f"{es} {me['pf']:6.3f} {me['dd']:6.1f}% {me['ret']:+7.1f}%")
print(f"  {'PESO IGUAL':<20} "
      f"{md_eq['score']}/4 {md_eq['pf']:6.3f} {md_eq['dd']:6.1f}% {md_eq['ret']:+7.1f}%  "
      f"{me_eq['score']}/4 {me_eq['pf']:6.3f} {me_eq['dd']:6.1f}% {me_eq['ret']:+7.1f}%")
print(f"  {'RISK PARITY':<20} "
      f"{md_rp['score']}/4 {md_rp['pf']:6.3f} {md_rp['dd']:6.1f}% {md_rp['ret']:+7.1f}%  "
      f"{me_rp['score']}/4 {me_rp['pf']:6.3f} {me_rp['dd']:6.1f}% {me_rp['ret']:+7.1f}%")

# ── correlaciones ─────────────────────────────────────────────────────────────
print(f"\nCORRELACIONES MENSUALES (periodo completo)")
corr = strats.corr().round(2)
print(corr.to_string())

# ═══════════════════════════════════════════════════════════════════════════
# GRAFICOS
# ═══════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(3, 1, figsize=(14, 12),
                          gridspec_kw={'height_ratios': [3, 3, 1]})
fig.suptitle('Portafolio 4 Estrategias · Cueva TIS', fontsize=13, fontweight='bold')

colors = {'BTC_EWMAC': '#f7931a', 'RSI2_QQQ': '#627eea',
          'IBB_QQQ': '#44dd88',   'RSI2_MTUM': '#aa66ff'}

# panel 1: estrategias individuales
ax1 = axes[0]
for name, series in strats.items():
    eq = (1 + series).cumprod()
    ax1.plot(eq.index, (eq - 1) * 100, color=colors[name], lw=1, label=name, alpha=0.7)
ax1.set_ylabel('Retorno (%)')
ax1.set_title('Estrategias individuales', fontsize=10)
ax1.legend(fontsize=8, loc='upper left')
ax1.axvline(split_t, color='#44aaff', lw=1.2, ls=':')
ax1.grid(alpha=0.15)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# panel 2: portafolio vs estrategias
ax2 = axes[1]
eq_eq = (1 + port_eq).cumprod()
eq_rp = (1 + port_rp).cumprod()
ax2.plot(eq_eq.index, (eq_eq - 1) * 100, color='#ffffff', lw=2,   label='Peso igual')
ax2.plot(eq_rp.index, (eq_rp - 1) * 100, color='#ffcc00', lw=2, ls='--', label='Risk parity')
ax2.set_facecolor('#111')
ax2.set_ylabel('Retorno (%)')
ax2.set_title('Portafolio combinado', fontsize=10)
ax2.legend(fontsize=9)
ax2.axvline(split_t, color='#44aaff', lw=1.2, ls=':')
ax2.grid(alpha=0.15)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# panel 3: drawdown del portafolio peso igual
ax3 = axes[2]
pk   = eq_eq.cummax()
dd_s = (eq_eq - pk) / pk * 100
ax3.fill_between(dd_s.index, dd_s, 0, color='#cc4444', alpha=0.7)
ax3.set_ylabel('Caida (%)')
ax3.axvline(split_t, color='#44aaff', lw=1.2, ls=':')
ax3.grid(alpha=0.15)
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.tight_layout()
out = '../resultados/curva_portafolio.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f'\nGrafico: {out}')
plt.show()
