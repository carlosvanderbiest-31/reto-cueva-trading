# AED fase 02 - Rotacion mensual por momentum entre clases de activo
import numpy as np, pandas as pd
RIESGO_UNIV=["SPY","QQQ","EFA","TLT","GLD","VNQ"]; LOOKBACK=12
SEMILLA=42; N_PLACEBO=1000

def cierre_mensual(s):
    d=pd.read_parquet(f"datos_limpios/norgate/D1/{s}.parquet").rename(columns={"datetime_servidor":"fecha"})
    d["fecha"]=pd.to_datetime(d["fecha"]); d=d.set_index("fecha").sort_index()
    return d["close"].resample("ME").last().rename(s)

panel=pd.concat([cierre_mensual(s) for s in RIESGO_UNIV], axis=1).dropna()
print("Periodo comun mensual:", panel.index[0].date(), "->", panel.index[-1].date(), "| meses:", len(panel))

mom=panel/panel.shift(LOOKBACK)-1           # momentum 12m
ret_next=panel.pct_change().shift(-1)       # retorno del mes siguiente
valido=mom.dropna().index
valido=[d for d in valido if d in ret_next.dropna(how="all").index]

filas=[]
for d in valido:
    if ret_next.loc[d].isna().any(): continue
    pick=mom.loc[d].idxmax()
    filas.append({"fecha":d, "pick":pick, "r_mom":ret_next.loc[d,pick],
                  "r_base":ret_next.loc[d].mean()})
res=pd.DataFrame(filas)
n=len(res); corte=int(n*0.70)
ins=res.iloc[:corte]
print(f"Meses con senal: {n} | corte 70% en {res['fecha'].iloc[corte].date()} | in-sample {ins['fecha'].iloc[0].date()}->{ins['fecha'].iloc[-1].date()} ({len(ins)})")

rm=ins["r_mom"].values; rb=ins["r_base"].values
ventaja=rm.mean()-rb.mean()
print(f"\nRetorno mensual medio: momentum {rm.mean()*100:.3f}% | promedio 6 clases {rb.mean()*100:.3f}% | dif {ventaja*100:+.3f}%")
# placebo: elegir al azar una de las 6 cada mes
rng=np.random.default_rng(SEMILLA); ins_ret=ret_next.loc[ins["fecha"]].values
sup=0
for _ in range(N_PLACEBO):
    idx=rng.integers(0,len(RIESGO_UNIV),size=len(ins))
    rand_ret=ins_ret[np.arange(len(ins)),idx]
    if np.nanmean(rand_ret)>=rm.mean(): sup+=1
pct=sup/N_PLACEBO
ins2=ins.copy(); ins2["anio"]=ins2["fecha"].dt.year
ra={a:g["r_mom"].mean() for a,g in ins2.groupby("anio") if len(g)>=5}
apos=sum(1 for v in ra.values() if v>0)
chk=[n>=30, ventaja>0, pct<0.05, (bool(ra) and apos>=len(ra)/2)]
print(f"\n=== JUICIO (horizonte 1 mes) ===")
print(f"1) Casos: {n} -> {'PASA' if chk[0] else 'FALLA'}")
print(f"2) Ventaja vs promedio de clases: {ventaja*100:+.3f}% -> {'PASA' if chk[1] else 'FALLA'}")
print(f"3) Placebo (elegir al azar): {pct*100:.1f}% iguala/supera -> {'PASA' if chk[2] else 'FALLA'} (<5%)")
print(f"4) Anios positivos: {apos}/{len(ra)} -> {'PASA' if chk[3] else 'FALLA'}")
print(f"\nVEREDICTO: {sum(chk)}/4")
