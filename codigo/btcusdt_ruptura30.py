# Fase 04 - Backtest BTC ruptura del maximo de 30 velas 4h (regla fase 03, sin cambios)
# 1% riesgo fijo, costes 0.1%/lado, 70% dentro / 30% fuera de muestra, caida vela a vela.
import numpy as np
import pandas as pd

RUTA = "datos/BTCUSDT_4h.csv"
VENTANA, ATR_N, MULT_STOP, RR, MAX_VELAS = 30, 14, 2.0, 2.0, 30
RIESGO, COSTE_LADO, CUENTA0 = 0.01, 0.001, 10000.0

df = pd.read_csv(RUTA, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
n = len(df)

# indicadores sobre toda la serie (sin mirar el futuro en la decision)
max_prev = pd.Series(h).rolling(VENTANA).max().shift(1).values
prev_c = pd.Series(c).shift(1)
tr = np.maximum(h - l, np.maximum((pd.Series(h) - prev_c).abs(), (pd.Series(l) - prev_c).abs()))
atr = tr.rolling(ATR_N).mean().values

corte = int(n * 0.70)
fecha_corte = df.loc[corte, "time"]

def simular(ini, fin):
    cuenta = CUENTA0
    equity = []          # (fecha, cuenta_mark_to_market)
    cierres = [CUENTA0]   # curva op por op
    ops = []
    t = ini
    while t < fin - 1:
        if not (c[t] > max_prev[t]) or np.isnan(atr[t]) or atr[t] <= 0:
            equity.append((df["time"].iloc[t], cuenta)); t += 1; continue
        entrada = o[t+1]
        riesgo_precio = MULT_STOP * atr[t]
        stop = entrada - riesgo_precio
        objetivo = entrada + RR * riesgo_precio
        if entrada <= stop:
            equity.append((df["time"].iloc[t], cuenta)); t += 1; continue
        riesgo_monto = RIESGO * cuenta
        unidades = riesgo_monto / (entrada - stop)
        coste_ent = COSTE_LADO * unidades * entrada
        k = t + 1
        salida = None
        while k < fin:
            # marca a mercado vela a vela (incluye la posicion abierta)
            mtm = cuenta + unidades * (c[k] - entrada) - coste_ent
            equity.append((df["time"].iloc[k], mtm))
            if l[k] <= stop:
                salida = stop; break                 # stop primero si coincide
            if h[k] >= objetivo:
                salida = objetivo; break
            if (k - (t+1)) >= MAX_VELAS:
                salida = c[k]; break
            k += 1
        if salida is None:
            salida = c[fin-1]; k = fin-1
        coste_sal = COSTE_LADO * unidades * salida
        pnl = unidades * (salida - entrada) - coste_ent - coste_sal
        cuenta += pnl
        cierres.append(cuenta)
        ops.append({"fecha": df["time"].iloc[t+1], "entrada": entrada, "salida": salida,
                    "r": pnl / riesgo_monto, "pnl": pnl})
        t = k + 1
    eq = pd.DataFrame(equity, columns=["fecha", "cuenta"])
    return cuenta, pd.DataFrame(ops), eq, np.array(cierres)

def metricas(ops, eq, cierres):
    r = ops["pnl"].values
    g = r[r > 0].sum(); p = -r[r < 0].sum()
    fb = g / p if p > 0 else float("inf")
    # FB sin la mejor operacion
    if len(r) > 1:
        rr = np.delete(r, np.argmax(r))
        g2 = rr[rr > 0].sum(); p2 = -rr[rr < 0].sum()
        fb_sin = g2 / p2 if p2 > 0 else float("inf")
    else:
        fb_sin = 0.0
    # caida vela a vela
    cv = eq["cuenta"].values
    dd_vela = ((cv - np.maximum.accumulate(cv)) / np.maximum.accumulate(cv)).min() * 100
    # caida op por op
    dd_op = ((cierres - np.maximum.accumulate(cierres)) / np.maximum.accumulate(cierres)).min() * 100
    return fb, fb_sin, len(r), dd_vela, dd_op

ini_dm = VENTANA + ATR_N
res = {}
for nombre, (ini, fin) in {"DM (70% dentro)": (ini_dm, corte), "FM (30% fuera)": (corte, n)}.items():
    cuenta, ops, eq, cierres = simular(ini, fin)
    fb, fb_sin, nops, dd_v, dd_o = metricas(ops, eq, cierres)
    res[nombre] = (ops, eq, cierres, fb, fb_sin, nops, dd_v, dd_o, cuenta)
    print(f"\n=== {nombre} === {df['time'].iloc[ini].date()} -> {df['time'].iloc[fin-1].date()}")
    print(f"Operaciones: {nops} | cuenta final: {cuenta:.0f} (desde {CUENTA0:.0f})")
    print(f"Factor beneficio: {fb:.2f} | FB sin mejor op: {fb_sin:.2f}")
    print(f"Caida max vela a vela: {dd_v:.1f}% | caida op por op: {dd_o:.1f}%")

# guardar resultados de FM + DM
ops_dm = res["DM (70% dentro)"][0].assign(tramo="DM")
ops_fm = res["FM (30% fuera)"][0].assign(tramo="FM")
pd.concat([ops_dm, ops_fm]).to_csv("resultados/btcusdt_ruptura30_operaciones.csv", index=False)
eq_dm = res["DM (70% dentro)"][1].assign(tramo="DM")
eq_fm = res["FM (30% fuera)"][1].assign(tramo="FM")
pd.concat([eq_dm, eq_fm]).to_csv("resultados/btcusdt_ruptura30_curva.csv", index=False)

# veredicto FUERA DE MUESTRA
_, _, _, fb, fb_sin, nops, dd_v, dd_o, _ = res["FM (30% fuera)"]
print("\n===== VEREDICTO FUERA DE MUESTRA (4 numeros TIS) =====")
chk = [("Factor beneficio >= 1.3", fb, fb >= 1.3),
       ("Operaciones >= 30", nops, nops >= 30),
       ("Caida maxima < 20%", abs(dd_v), abs(dd_v) < 20),
       ("FB sin mejor op > 1", fb_sin, fb_sin > 1)]
for nombre, val, ok in chk:
    print(f"  {'PASA' if ok else 'FALLA'} - {nombre}: {val:.2f}")
print(f"\nVEREDICTO: {sum(ok for _,_,ok in chk)}/4")
