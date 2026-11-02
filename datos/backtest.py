import pandas as pd
import numpy as np

# ── CONFIG ─────────────────────────────────────────────────────────────────
COST_RT   = 0.0015   # 0.15% roundtrip — Binance Futures taker
SPLIT     = 0.70     # 70% in-sample / 30% out-of-sample
PIVOT_N   = 5        # velas a cada lado para confirmar pivote (H1)

# ── DATOS ──────────────────────────────────────────────────────────────────
df = pd.read_csv('BTCUSDT_4h.csv', parse_dates=['time'])
for c in ['open','high','low','close','volume']:
    df[c] = df[c].astype(float)
df = df.reset_index(drop=True)

split_i = int(len(df) * SPLIT)
print(f"Velas totales : {len(df)}")
print(f"Dentro muestra: {df.loc[0,'time'].date()} -> {df.loc[split_i-1,'time'].date()} ({split_i} velas)")
print(f"Fuera muestra : {df.loc[split_i,'time'].date()} -> {df.loc[len(df)-1,'time'].date()} ({len(df)-split_i} velas)\n")

# ── METRICAS ───────────────────────────────────────────────────────────────
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
        print(f"\n{label}: sin operaciones fuera de muestra.\n")
        return
    fb     = profit_factor(pnls)
    n      = len(pnls)
    dd     = max_dd(pnls)
    pnls_nb = sorted(pnls)[:-1] if len(pnls) > 1 else pnls
    fb_nb  = profit_factor(pnls_nb)
    check  = lambda ok: "OK" if ok else "XX"
    passed = sum([fb >= 1.3, n >= 30, dd < 20, fb_nb > 1])
    wins   = sum(1 for p in pnls if p > 0)
    print(f"{'='*54}")
    print(f"  {label}")
    print(f"  Fuera de muestra | costes {COST_RT*100:.2f}% roundtrip")
    print(f"{'='*54}")
    print(f"  Factor de beneficio          {fb:6.3f}  {check(fb>=1.3)}  (>=1.3)")
    print(f"  Operaciones                  {n:6d}  {check(n>=30)}  (>=30)")
    print(f"  Caida maxima                 {dd:5.1f}%  {check(dd<20)}  (<20%)")
    print(f"  FB sin mejor operacion       {fb_nb:6.3f}  {check(fb_nb>1)}  (>1)")
    print(f"{'='*54}")
    print(f"  Ganadoras: {wins}/{n} ({wins/n*100:.0f}%)")
    print(f"  VEREDICTO: {passed}/4  {'APRUEBA' if passed==4 else 'NO APRUEBA'}")
    print(f"{'='*54}\n")
    return passed, fb, n, dd, fb_nb

# ══════════════════════════════════════════════════════════════════════════════
# HIPOTESIS 1 — Doble Techo con Divergencia de Volumen (SHORT)
# ══════════════════════════════════════════════════════════════════════════════
print("Ejecutando H1 — Doble Techo con Divergencia de Volumen...")

# Pre-calcular pivotes altos (necesitan 5 velas antes y 5 despues)
is_pivot = [False] * len(df)
for i in range(PIVOT_N, len(df) - PIVOT_N):
    h = df.loc[i, 'high']
    if h > df.loc[i-PIVOT_N:i-1, 'high'].max() and h > df.loc[i+1:i+PIVOT_N, 'high'].max():
        is_pivot[i] = True

trades_h1 = []
state   = 'BUSCANDO_M1'
M1 = VOL_M1 = SWING_LOW = None
NIVEL_ENTRADA = STOP = DISTANCIA = OBJ1 = OBJ2 = None
VELAS_ESP = 0
PARTIAL   = False
entry_p   = part_p = entry_i = None

for i in range(len(df)):
    row = df.loc[i]

    if state == 'BUSCANDO_M1':
        if is_pivot[i]:
            M1 = row['high']; VOL_M1 = row['volume']
            SWING_LOW = row['low']; state = 'BUSCANDO_M2'

    elif state == 'BUSCANDO_M2':
        if row['low'] < SWING_LOW:
            SWING_LOW = row['low']
        # Si hay un pivote mas alto, resetear M1
        if is_pivot[i] and row['high'] > M1:
            M1 = row['high']; VOL_M1 = row['volume']
            SWING_LOW = row['low']; continue
        retroceso = (M1 - SWING_LOW) / M1
        if retroceso < 0.015:
            continue
        if row['high'] >= M1 and row['volume'] < 0.7 * VOL_M1:
            M2 = row['high']
            NIVEL_ENTRADA = row['low']
            STOP    = max(M1, M2) * 1.01
            DIST    = STOP - NIVEL_ENTRADA
            OBJ1    = NIVEL_ENTRADA - DIST        # 1:1
            OBJ2    = SWING_LOW
            if OBJ2 >= NIVEL_ENTRADA:             # objetivo debajo de entrada
                state = 'BUSCANDO_M1'; continue
            VELAS_ESP = 0; PARTIAL = False
            state = 'ESPERANDO_RUPTURA'

    elif state == 'ESPERANDO_RUPTURA':
        VELAS_ESP += 1
        if VELAS_ESP > 10:
            state = 'BUSCANDO_M1'; continue
        if row['low'] < NIVEL_ENTRADA:
            entry_p = NIVEL_ENTRADA; entry_i = i
            state = 'DENTRO'

    elif state == 'DENTRO':
        # a. Stop
        if row['high'] >= STOP:
            sl_pnl = (entry_p - STOP) / entry_p
            if PARTIAL:
                pnl = (entry_p - part_p) / entry_p * 0.5 + sl_pnl * 0.5 - COST_RT
            else:
                pnl = sl_pnl - COST_RT
            trades_h1.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= split_i})
            state = 'BUSCANDO_M1'
        # b. Objetivo parcial
        elif not PARTIAL and row['low'] <= OBJ1:
            PARTIAL = True; part_p = OBJ1
        # c. Objetivo final
        elif PARTIAL and row['low'] <= OBJ2:
            pnl = ((entry_p - part_p) / entry_p * 0.5 +
                   (entry_p - OBJ2)   / entry_p * 0.5 - COST_RT)
            trades_h1.append({'i': entry_i, 'pnl': pnl, 'oos': entry_i >= split_i})
            state = 'BUSCANDO_M1'

oos_h1 = [t for t in trades_h1 if t['oos']]
r1 = show("H1 — Doble Techo Divergencia Volumen (SHORT)", oos_h1)

# ══════════════════════════════════════════════════════════════════════════════
# HIPOTESIS 2 — Pullback MA200 (LONG)
# ══════════════════════════════════════════════════════════════════════════════
print("Ejecutando H2 — Pullback en tendencia MA200...")

trades_h2 = []
state2    = 'BUSCANDO'
entry_p2  = stop2 = entry_i2 = None

for i in range(200, len(df)):
    row = df.loc[i]
    prev = df.loc[:i-1]

    if state2 == 'ENTRADA_PENDIENTE':
        entry_p2 = row['open']
        stop2    = entry_p2 * 0.98
        entry_i2 = i
        state2   = 'DENTRO'

    if state2 == 'DENTRO':
        max7 = df.loc[i-7:i-1, 'high'].max()
        # a. Stop
        if row['low'] <= stop2:
            pnl = (stop2 - entry_p2) / entry_p2 - COST_RT
            trades_h2.append({'i': entry_i2, 'pnl': pnl, 'oos': entry_i2 >= split_i})
            state2 = 'BUSCANDO'
        # b. Salida objetivo
        elif row['close'] > max7:
            pnl = (row['close'] - entry_p2) / entry_p2 - COST_RT
            trades_h2.append({'i': entry_i2, 'pnl': pnl, 'oos': entry_i2 >= split_i})
            state2 = 'BUSCANDO'

    if state2 == 'BUSCANDO':
        ma200 = df.loc[i-200:i-1, 'close'].mean()
        min7  = df.loc[i-7:i-1,   'low'].min()
        if row['close'] < min7 and row['close'] > ma200:
            state2 = 'ENTRADA_PENDIENTE'

oos_h2 = [t for t in trades_h2 if t['oos']]
r2 = show("H2 — Pullback MA200 (LONG)", oos_h2)
