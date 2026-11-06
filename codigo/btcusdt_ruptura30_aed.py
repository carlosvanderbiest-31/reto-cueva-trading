# AED fase 02 - BTC ruptura del maximo de 30 velas 4h
# Mide si tras marcar nuevo maximo de 30 velas, el retorno a 20 velas supera al de cualquier vela.
# Sin pre-registro: 4 condiciones TIS. Corte 70/30, solo se mira el 70% mas antiguo.
import numpy as np
import pandas as pd

RUTA = "datos/BTCUSDT_4h.csv"
VENTANA = 30          # velas para el maximo previo (ruptura)
HORIZONTES = [1, 5, 20]
H_JUICIO = 20         # horizonte declarado antes de medir
COSTE_LADO = 0.001    # 0.1% por lado (supuesto)
COSTE_RT = 2 * COSTE_LADO
SEMILLA = 42
N_PLACEBO = 1000

df = pd.read_csv(RUTA, parse_dates=["time"])
df = df.sort_values("time").reset_index(drop=True)
n = len(df)
corte = int(n * 0.70)
fecha_corte = df.loc[corte, "time"]
ins = df.iloc[:corte].reset_index(drop=True)   # 70% in-sample
print(f"Velas totales: {n} | corte 70% en indice {corte} | fecha corte: {fecha_corte}")
print(f"In-sample: {ins['time'].iloc[0]} -> {ins['time'].iloc[-1]} ({len(ins)} velas)")

high = ins["high"].values
close = ins["close"].values

# senal: cierre actual > maximo de los high de las 30 velas ANTERIORES
max_prev = pd.Series(high).rolling(VENTANA).max().shift(1).values
senal = close > max_prev
senal[:VENTANA] = False

def ret_fwd(h):
    r = np.full(len(close), np.nan)
    r[:-h] = close[h:] / close[:-h] - 1.0
    return r

print("\n--- Retornos forward (media, netos de coste round-trip) ---")
print(f"{'H':>4} | {'n_senal':>8} | {'media_senal':>12} | {'media_base':>11} | {'dif':>9}")
for h in HORIZONTES:
    r = ret_fwd(h)
    mask = senal & ~np.isnan(r)
    rs = r[mask] - COSTE_RT          # senal neta de costes
    rb = r[~np.isnan(r)] - COSTE_RT  # cualquier vela, neta de costes
    print(f"{h:>4} | {mask.sum():>8} | {rs.mean():>12.5f} | {rb.mean():>11.5f} | {rs.mean()-rb.mean():>9.5f}")

# ----- Juicio en H_JUICIO con las 4 condiciones -----
h = H_JUICIO
r = ret_fwd(h)
mask = senal & ~np.isnan(r)
rs = r[mask] - COSTE_RT
base_all = r[~np.isnan(r)] - COSTE_RT
n_casos = int(mask.sum())
ventaja = rs.mean() - base_all.mean()

# placebo: 1000 sorteos de n_casos velas al azar, cuantos igualan o superan la media senal
rng = np.random.default_rng(SEMILLA)
pool = r[~np.isnan(r)]
idx_validos = np.where(~np.isnan(r))[0]
sup = 0
for _ in range(N_PLACEBO):
    pick = rng.choice(pool, size=n_casos, replace=False)
    if (pick - COSTE_RT).mean() >= rs.mean():
        sup += 1
pct_placebo = sup / N_PLACEBO

# por anio: media de la senal positiva, con 5+ casos
ins_s = ins.copy()
ins_s["r"] = r
ins_s["senal"] = senal
ins_s["anio"] = ins_s["time"].dt.year
res_anio = {}
for anio, g in ins_s[ins_s["senal"] & ~ins_s["r"].isna()].groupby("anio"):
    if len(g) >= 5:
        res_anio[anio] = (g["r"].mean() - COSTE_RT)
anios_con_casos = len(res_anio)
anios_pos = sum(1 for v in res_anio.values() if v > 0)

print(f"\n=== JUICIO en H={h} velas (coste {COSTE_RT*100:.1f}% round-trip) ===")
print(f"1) Casos: {n_casos}  -> {'PASA' if n_casos>=30 else 'FALLA'} (>=30)")
print(f"2) Ventaja neta vs cualquier vela: senal {rs.mean()*100:.3f}% vs base {base_all.mean()*100:.3f}% "
      f"= {ventaja*100:+.3f}%  -> {'PASA' if ventaja>0 else 'FALLA'}")
print(f"3) Placebo: {pct_placebo*100:.1f}% de 1000 sorteos iguala/supera  -> {'PASA' if pct_placebo<0.05 else 'FALLA'} (<5%)")
print(f"4) Anios positivos: {anios_pos}/{anios_con_casos}  -> {'PASA' if anios_con_casos>0 and anios_pos>=anios_con_casos/2 else 'FALLA'} (>=mitad)")
print("   Detalle por anio:", {a: round(v*100,2) for a,v in res_anio.items()})

pasa = [n_casos>=30, ventaja>0, pct_placebo<0.05, (anios_con_casos>0 and anios_pos>=anios_con_casos/2)]
print(f"\nVEREDICTO: {sum(pasa)}/4 condiciones")
