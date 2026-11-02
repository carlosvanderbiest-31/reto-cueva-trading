"""
T20M - Top 20 Momentum S&P 500
Ranking mensual por momentum 12m ajustado por volatilidad 6m.
Selecciona las 20 acciones con mayor score, peso igual, rebalanceo mensual.

ADVERTENCIA: usa el S&P 500 ACTUAL (sesgo de supervivencia).
Los resultados reales de T20M son probablemente algo menores.

Split : 70/30
Coste : 0.15% por operacion individual (compra o venta)
"""
import pandas as pd
import numpy as np
import yfinance as yf
import os, warnings
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
warnings.filterwarnings('ignore')

COST    = 0.00075   # 0.075% por lado (compra O venta, no roundtrip completo)
SPLIT   = 0.70
TOP_N   = 20
CACHE   = 'sp500_prices.pkl'
import pickle

# ── 1. obtener tickers del S&P 500 desde Wikipedia ───────────────────────────
print("Obteniendo tickers del S&P 500 desde Wikipedia...")
try:
    import requests
    html = requests.get(
        'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    ).text
    tables = pd.read_html(html)
    sp500  = tables[0]['Symbol'].str.replace('.', '-', regex=False).tolist()
    print(f"  {len(sp500)} tickers encontrados")
except Exception as e:
    print(f"  Error Wikipedia: {e}. Usando lista de respaldo.")
    # lista de respaldo con los 50 mas grandes por peso
    sp500 = [
        'AAPL','MSFT','NVDA','AMZN','META','GOOGL','GOOG','BRK-B','LLY','AVGO',
        'TSLA','JPM','UNH','V','XOM','MA','COST','HD','PG','JNJ',
        'ABBV','MRK','WMT','BAC','NFLX','CRM','CVX','KO','PEP','AMD',
        'TMO','LIN','ACN','MCD','CSCO','ABT','DHR','ADBE','NKE','TXN',
        'NEE','PM','UPS','RTX','ORCL','HON','AMGN','INTU','QCOM','GS',
        'CAT','SPGI','BKNG','ISRG','AXP','BLK','SYK','T','MDT','GILD',
        'BMY','VRTX','PFE','DE','CB','MMC','ELV','CI','SO','MO',
        'DUK','APD','ZTS','AON','ITW','ETN','SHW','CME','PLD','PSA',
        'AMT','WM','CTAS','ADI','KLAC','LRCX','MCHP','AMAT','MU','PANW',
        'CRWD','SNOW','NOW','DDOG','ZS','NET','FTNT','OKTA','UBER','ABNB'
    ]

# ── 2. descargar / cargar precios ────────────────────────────────────────────
if os.path.exists(CACHE):
    print(f"Cargando precios desde cache ({CACHE})...")
    with open(CACHE, 'rb') as f:
        prices = pickle.load(f)
else:
    print(f"Descargando precios de {len(sp500)} tickers (puede tardar 3-5 min)...")
    batch_size = 50
    frames = []
    for i in range(0, len(sp500), batch_size):
        batch = sp500[i:i+batch_size]
        print(f"  Lote {i//batch_size + 1}/{(len(sp500)+batch_size-1)//batch_size}: {batch[0]}..{batch[-1]}")
        try:
            raw = yf.download(batch, start='2005-01-01', auto_adjust=True,
                              progress=False, group_by='ticker', threads=True)
            if len(batch) == 1:
                c = raw['Close'].to_frame(name=batch[0])
            else:
                c = raw['Close'] if 'Close' in raw.columns else raw.xs('Close', axis=1, level=1)
            frames.append(c)
        except Exception as e:
            print(f"    Error lote: {e}")
    prices = pd.concat(frames, axis=1)
    prices = prices.loc[:, ~prices.columns.duplicated()]
    prices.index = pd.to_datetime(prices.index)
    with open(CACHE, 'wb') as f:
        pickle.dump(prices, f)
    print(f"  Cache guardado. Shape: {prices.shape}")

prices = prices.sort_index()
# eliminar columnas con demasiados NaN (acciones que no existian en 2005)
prices = prices.dropna(thresh=int(len(prices)*0.5), axis=1)
print(f"\nUniverso: {prices.shape[1]} acciones · {prices.index[0].date()} a {prices.index[-1].date()}")

# ── 3. calcular scores mensuales ─────────────────────────────────────────────
print("\nCalculando scores de momentum mensual...")

# resamplear al ultimo dia de cada mes
monthly = prices.resample('ME').last()

# retorno 12m excluyendo el ultimo mes (Jegadeesh-Titman standard)
ret_12m = monthly.pct_change(12).shift(1)   # ret de hace 12m a hace 1m

# volatilidad 6m de retornos diarios, resampleada al mes
daily_ret = prices.pct_change()
vol_6m = daily_ret.rolling(126).std() * np.sqrt(252)
vol_monthly = vol_6m.resample('ME').last()

# score = ret_12m / vol_6m (momentum ajustado por riesgo)
score = ret_12m / vol_monthly.replace(0, np.nan)

# alinear indices
idx = score.index.intersection(monthly.index)
score   = score.loc[idx]
monthly = monthly.loc[idx]

print(f"Meses con scores: {len(score)}")

# ── 4. backtest mensual ──────────────────────────────────────────────────────
split_i = int(len(idx) * SPLIT)
split_t = idx[split_i]
print(f"Diseno : {idx[0].date()} a {idx[split_i-1].date()}")
print(f"Examen : {idx[split_i].date()} a {idx[-1].date()}")

# cargar SPY para filtro de mercado
spy_daily = pd.read_csv('spy_1d_yahoo.csv', parse_dates=['fecha'], index_col='fecha')['close']
spy_ma200_daily = spy_daily.rolling(200).mean()
spy_monthly_close = spy_daily.resample('ME').last()
spy_ma200_monthly = spy_ma200_daily.resample('ME').last()

def run_t20m(use_spy_filter=False):
    portfolio_returns = []
    holding = set()
    in_cash = False

    for k in range(1, len(idx)):
        date      = idx[k]
        prev_date = idx[k-1]
        sc        = score.loc[date].dropna()

        if len(sc) < TOP_N:
            continue

        # filtro SPY MA200
        spy_ok = True
        if use_spy_filter and date in spy_monthly_close.index and date in spy_ma200_monthly.index:
            spy_ok = spy_monthly_close.loc[date] > spy_ma200_monthly.loc[date]

        top20_new = set(sc.nlargest(TOP_N).index) if spy_ok else set()
        is_cash   = len(top20_new) == 0

        if holding and not in_cash:
            prices_prev = monthly.loc[prev_date, list(holding)]
            prices_curr = monthly.loc[date, list(holding)]
            valid = prices_prev.notna() & prices_curr.notna() & (prices_prev > 0)
            if valid.sum() > 0:
                rets = (prices_curr[valid] - prices_prev[valid]) / prices_prev[valid]
                salidas  = holding - top20_new
                entradas = top20_new - holding
                coste_mes = (len(salidas) + len(entradas)) * COST / TOP_N
                ret_mes = rets.mean() - coste_mes
                portfolio_returns.append({
                    'fecha': date, 'ret': ret_mes,
                    'oos': prev_date >= split_t,
                })
        elif in_cash and not is_cash:
            portfolio_returns.append({
                'fecha': date, 'ret': -COST,
                'oos': prev_date >= split_t,
            })

        holding   = top20_new
        in_cash   = is_cash

    return portfolio_returns

spy_ma200_monthly_100 = spy_ma200_daily.copy()  # reuse variable name below

# recalcular con MA100
spy_ma100_daily   = spy_daily.rolling(100).mean()
spy_ma100_monthly = spy_ma100_daily.resample('ME').last()

def run_t20m_v2(spy_ma_monthly, label):
    portfolio_returns = []
    holding = set()
    in_cash = False
    for k in range(1, len(idx)):
        date      = idx[k]
        prev_date = idx[k-1]
        sc        = score.loc[date].dropna()
        if len(sc) < TOP_N:
            continue
        spy_ok = True
        if date in spy_monthly_close.index and date in spy_ma_monthly.index:
            spy_ok = spy_monthly_close.loc[date] > spy_ma_monthly.loc[date]
        top20_new = set(sc.nlargest(TOP_N).index) if spy_ok else set()
        is_cash   = len(top20_new) == 0
        if holding and not in_cash:
            prices_prev = monthly.loc[prev_date, list(holding)]
            prices_curr = monthly.loc[date, list(holding)]
            valid = prices_prev.notna() & prices_curr.notna() & (prices_prev > 0)
            if valid.sum() > 0:
                rets = (prices_curr[valid] - prices_prev[valid]) / prices_prev[valid]
                salidas  = holding - top20_new
                entradas = top20_new - holding
                coste_mes = (len(salidas) + len(entradas)) * COST / TOP_N
                portfolio_returns.append({'fecha': date,
                    'ret': rets.mean() - coste_mes,
                    'oos': prev_date >= split_t})
        elif in_cash and not is_cash:
            portfolio_returns.append({'fecha': date, 'ret': -COST,
                                      'oos': prev_date >= split_t})
        holding = top20_new
        in_cash = is_cash
    return portfolio_returns

print("\nVersion SIN filtro SPY:")
pr_base = run_t20m(use_spy_filter=False)
print(f"  Meses: {len(pr_base)}")

print("Version CON filtro SPY MA200:")
pr_spy  = run_t20m(use_spy_filter=True)
print(f"  Meses: {len(pr_spy)}")

print("Version CON filtro SPY MA100:")
pr_spy100 = run_t20m_v2(spy_ma100_monthly, 'MA100')
print(f"  Meses: {len(pr_spy100)}")

# ── 5. metricas TIS ──────────────────────────────────────────────────────────
def metrics(rets_mensuales, label, verbose=True):
    if not rets_mensuales:
        print(f"  {label}: sin datos"); return None
    # convertir retornos mensuales a "trades" para PF
    # PF = suma ganancias / suma perdidas
    pnls = rets_mensuales
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
    # para T20M: "operaciones" = meses (cada mes es 1 rebalanceo = 1 "operacion de portafolio")
    score_val = sum([pf>=1.3, n>=30, dd<0.20, pf_nb>1])
    if verbose:
        print(f"  PF (mensual)    {pf:6.3f}  {ok(pf>=1.3)}  (>=1.30)")
        print(f"  Meses           {n:6d}  {ok(n>=30)}  (>=30)")
        print(f"  DD max.       {dd*100:6.1f}%  {ok(dd<0.20)}  (<20%)")
        print(f"  PF sin mejor    {pf_nb:6.3f}  {ok(pf_nb>1)}  (>1)")
        print(f"  Acierto        {wins/n*100:5.1f}%  (meses positivos)")
        print(f"  Retorno        {ret:+.1f}%")
        print(f"  VEREDICTO {score_val}/4  {'APRUEBA' if score_val==4 else 'NO APRUEBA'}")
    return dict(pf=pf, n=n, dd=dd*100, pf_nb=pf_nb, score=score_val, ret=ret)

print(f"\n{'='*55}")
print("T20M - Top 20 Momentum S&P 500")
print("NOTA: sesgo de supervivencia (universo S&P 500 actual)")
print(f"{'='*55}")

for label, pr in [("SIN filtro SPY", pr_base), ("CON filtro SPY MA200", pr_spy), ("CON filtro SPY MA100", pr_spy100)]:
    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")
    dis_rets = [r['ret'] for r in pr if not r['oos']]
    exa_rets = [r['ret'] for r in pr if r['oos']]
    print("-- DISENO --")
    metrics(dis_rets, 'diseno')
    print("-- EXAMEN --")
    metrics(exa_rets, 'examen')

# usar version con SPY MA100 para la curva
portfolio_returns = pr_spy100
dis_rets = [r['ret'] for r in portfolio_returns if not r['oos']]
exa_rets = [r['ret'] for r in portfolio_returns if r['oos']]
md = metrics(dis_rets, 'diseno', verbose=False)
me = metrics(exa_rets, 'examen', verbose=False)

# ── 6. comparacion con SPY (buy & hold) ──────────────────────────────────────
spy = pd.read_csv('spy_1d_yahoo.csv', parse_dates=['fecha'], index_col='fecha')['close']
spy_monthly = spy.resample('ME').last()
spy_ret = spy_monthly.pct_change().dropna()

# ── 7. curva de equity ───────────────────────────────────────────────────────
port_df = pd.DataFrame(portfolio_returns).set_index('fecha') if portfolio_returns else pd.DataFrame({'ret':[],'fecha':[]}).set_index('fecha')
eq_vals  = (1 + port_df['ret']).cumprod()
eq_vals.iloc[0:0]  # no-op

# base 1.0 desde el inicio
base = pd.Series([1.0], index=[idx[0]])
eq_s = pd.concat([base, (1 + port_df['ret']).cumprod()])

spy_m2 = spy_monthly.loc[eq_s.index[0]:]
spy_norm = spy_m2 / spy_m2.iloc[0]

fig, axes = plt.subplots(2, 1, figsize=(14,8), gridspec_kw={'height_ratios':[3,1]})
fig.suptitle('T20M · Top 20 Momentum S&P 500 (sesgo supervivencia)', fontsize=11, fontweight='bold')

ax = axes[0]
ax.plot(eq_s.index, (eq_s-1)*100, color='#f0c040', lw=1.5, label='T20M')
ax.plot(spy_norm.index, (spy_norm-1)*100, color='#888', lw=1, ls='--', label='SPY B&H')
ax.axvline(split_t, color='#44aaff', lw=1, ls=':', label='Inicio examen')
ax.set_ylabel('Retorno (%)'); ax.legend(fontsize=9); ax.grid(alpha=0.2)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

pk   = eq_s.cummax()
dd_s = (eq_s - pk) / pk * 100
axes[1].fill_between(dd_s.index, dd_s, 0, color='#cc4444', alpha=0.6)
axes[1].set_ylabel('Caida (%)'); axes[1].grid(alpha=0.2)
axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.tight_layout()
out = '../resultados/curva_t20m.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f'\nGrafico: {out}')
plt.show()
