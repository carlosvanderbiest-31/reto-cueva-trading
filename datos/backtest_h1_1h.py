import pandas as pd
import numpy as np

# ── CONFIG ─────────────────────────────────────────────────────────────────
COST_RT  = 0.0015   # 0.15% roundtrip — Binance Futures taker
SPLIT    = 0.70
PIVOT_N  = 5
VOL_THR  = 0.70     # M2 volume < 70% of M1
MIN_RET  = 0.015    # retroceso minimo 1.5%
MAX_WAIT = 10       # velas max para esperar entrada

SYMBOLS = ['BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT']

# ── HELPERS ────────────────────────────────────────────────────────────────
def profit_factor(pnls):
    w = sum(p for p in pnls if p > 0)
    l = abs(sum(p for p in pnls if p <= 0))
    return (w / l) if l > 0 else (float('inf') if w > 0 else 0)

def max_dd(pnls):
    eq, peak, worst = 1.0, 1.0, 0.0
    for p in pnls:
        eq *= (1 + p)
        peak = max(peak, eq)
        worst = max(worst, (peak - eq) / peak)
    return worst * 100

def show(label, trades_oos):
    pnls = [t['pnl'] for t in trades_oos]
    if not pnls:
        print(f"  {label}: sin operaciones fuera de muestra.\n")
        return None
    fb    = profit_factor(pnls)
    n     = len(pnls)
    dd    = max_dd(pnls)
    nb    = sorted(pnls)[:-1] if len(pnls) > 1 else pnls
    fb_nb = profit_factor(nb)
    ok    = lambda v: "OK" if v else "XX"
    pasa  = sum([fb>=1.3, n>=30, dd<20, fb_nb>1])
    wins  = sum(1 for p in pnls if p > 0)
    print(f"  {'─'*50}")
    print(f"  {label}")
    print(f"  {'─'*50}")
    print(f"  FB                  {fb:6.3f}   {ok(fb>=1.3)}  (>=1.3)")
    print(f"  Operaciones         {n:6d}   {ok(n>=30)}  (>=30)")
    print(f"  Caida max           {dd:5.1f}%   {ok(dd<20)}  (<20%)")
    print(f"  FB sin mejor        {fb_nb:6.3f}   {ok(fb_nb>1)}  (>1)")
    print(f"  Ganadoras           {wins}/{n} ({wins/n*100:.0f}%)")
    print(f"  VEREDICTO           {pasa}/4  {'APRUEBA' if pasa==4 else 'NO APRUEBA'}")
    print()
    return {'fb':fb,'n':n,'dd':dd,'fb_nb':fb_nb,'pasa':pasa,'trades':trades_oos}

# ── BACKTEST H1 POR SIMBOLO ────────────────────────────────────────────────
def run_h1(symbol):
    fname = f"{symbol}_1h.csv"
    df = pd.read_csv(fname, parse_dates=['time'])
    for c in ['open','high','low','close','volume']:
        df[c] = df[c].astype(float)
    df = df.reset_index(drop=True)

    split_i = int(len(df) * SPLIT)

    # Pre-calcular pivotes altos
    is_pivot = [False]*len(df)
    for i in range(PIVOT_N, len(df)-PIVOT_N):
        h = df.loc[i,'high']
        if (h > df.loc[i-PIVOT_N:i-1,'high'].max() and
            h > df.loc[i+1:i+PIVOT_N,'high'].max()):
            is_pivot[i] = True

    trades = []
    state  = 'BUSCANDO_M1'
    M1=VOL_M1=SWING_LOW=None
    NIVEL_ENTRADA=STOP=OBJ1=OBJ2=None
    VELAS_ESP=0; PARTIAL=False
    entry_p=part_p=entry_i=None

    for i in range(len(df)):
        row = df.loc[i]

        if state == 'BUSCANDO_M1':
            if is_pivot[i]:
                M1=row['high']; VOL_M1=row['volume']
                SWING_LOW=row['low']; state='BUSCANDO_M2'

        elif state == 'BUSCANDO_M2':
            if row['low'] < SWING_LOW:
                SWING_LOW = row['low']
            if is_pivot[i] and row['high'] > M1:
                M1=row['high']; VOL_M1=row['volume']
                SWING_LOW=row['low']; continue
            if (M1 - SWING_LOW) / M1 < MIN_RET:
                continue
            if row['high'] >= M1 and row['volume'] < VOL_THR * VOL_M1:
                M2 = row['high']
                NIVEL_ENTRADA = row['low']
                STOP = max(M1, M2) * 1.01
                DIST = STOP - NIVEL_ENTRADA
                OBJ1 = NIVEL_ENTRADA - DIST
                OBJ2 = SWING_LOW
                if OBJ2 >= NIVEL_ENTRADA:
                    state='BUSCANDO_M1'; continue
                VELAS_ESP=0; PARTIAL=False
                state='ESPERANDO_RUPTURA'

        elif state == 'ESPERANDO_RUPTURA':
            VELAS_ESP += 1
            if VELAS_ESP > MAX_WAIT:
                state='BUSCANDO_M1'; continue
            if row['low'] < NIVEL_ENTRADA:
                entry_p=NIVEL_ENTRADA; entry_i=i; state='DENTRO'

        elif state == 'DENTRO':
            if row['high'] >= STOP:
                sl = (entry_p - STOP) / entry_p
                if PARTIAL:
                    pnl = (entry_p-part_p)/entry_p*0.5 + sl*0.5 - COST_RT
                else:
                    pnl = sl - COST_RT
                trades.append({'sym':symbol,'i':entry_i,'time':df.loc[entry_i,'time'],
                                'pnl':pnl,'oos':entry_i>=split_i,'tipo':'stop'})
                state='BUSCANDO_M1'
            elif not PARTIAL and row['low'] <= OBJ1:
                PARTIAL=True; part_p=OBJ1
            elif PARTIAL and row['low'] <= OBJ2:
                pnl = ((entry_p-part_p)/entry_p*0.5 +
                       (entry_p-OBJ2)/entry_p*0.5 - COST_RT)
                trades.append({'sym':symbol,'i':entry_i,'time':df.loc[entry_i,'time'],
                                'pnl':pnl,'oos':entry_i>=split_i,'tipo':'obj'})
                state='BUSCANDO_M1'

    oos = [t for t in trades if t['oos']]
    print(f"  {symbol:<12} total:{len(trades):3d}  OOS:{len(oos):3d}")
    return trades

# ── MAIN ───────────────────────────────────────────────────────────────────
print("H1 — Doble Techo Divergencia Volumen | 1H | 5 activos")
print(f"Costes: {COST_RT*100:.2f}% roundtrip | Split 70/30\n")

print("Trades por simbolo:")
all_trades = []
for sym in SYMBOLS:
    all_trades += run_h1(sym)

print()

# ── POR SIMBOLO ────────────────────────────────────────────────────────────
print("=" * 54)
print("RESULTADOS POR SIMBOLO (fuera de muestra)\n")
for sym in SYMBOLS:
    oos = [t for t in all_trades if t['sym']==sym and t['oos']]
    show(sym, oos)

# ── PORTAFOLIO COMBINADO ───────────────────────────────────────────────────
print("=" * 54)
print("PORTAFOLIO COMBINADO — 5 activos en 1H\n")
oos_all = sorted([t for t in all_trades if t['oos']], key=lambda x: x['time'])
show("PORTAFOLIO COMBINADO", oos_all)
