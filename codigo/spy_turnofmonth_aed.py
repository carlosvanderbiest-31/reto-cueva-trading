# AED fase 02 - S&P 500 (SPY), efecto cambio de mes (turn-of-month)
# Ventana TOM = ultimo dia de mes + primeros 3 del siguiente. Comportamiento: retorno diario TOM > dia cualquiera.
import numpy as np, pandas as pd
RUTA="datos/spy_1d_yahoo.csv"; SEMILLA=42; N_PLACEBO=1000; COSTE_RT=2*0.0003

df=pd.read_csv(RUTA, parse_dates=["fecha"]).sort_values("fecha").reset_index(drop=True)
df["ret"]=df["close"].pct_change()
df["ym"]=df["fecha"].dt.to_period("M")
g=df.groupby("ym")
df["pos_asc"]=g.cumcount()               # 0 = primer dia de bolsa del mes
df["n_mes"]=g["close"].transform("size")
df["pos_desc"]=df["n_mes"]-1-df["pos_asc"]  # 0 = ultimo dia del mes
df["tom"]=(df["pos_asc"]<=2)|(df["pos_desc"]==0)   # primeros 3 + ultimo

n=len(df); corte=int(n*0.70); fecha_corte=df.loc[corte,"fecha"]
ins=df.iloc[:corte].dropna(subset=["ret"]).copy()
print(f"Velas totales: {n} | corte 70% en {fecha_corte.date()}")
print(f"In-sample: {ins['fecha'].iloc[0].date()} -> {ins['fecha'].iloc[-1].date()} ({len(ins)} dias)")

rt=ins.loc[ins["tom"],"ret"].values
ra=ins["ret"].values
nc=len(rt); ventaja=rt.mean()-ra.mean()
print(f"\nRetorno diario medio: TOM {rt.mean()*100:.4f}% | cualquier dia {ra.mean()*100:.4f}% | dif {ventaja*100:+.4f}%")
print(f"Dias TOM: {nc} ({nc/len(ins)*100:.0f}% de los dias) | ganan {(rt>0).mean()*100:.1f}% de las veces vs {(ra>0).mean()*100:.1f}%")

rng=np.random.default_rng(SEMILLA); sup=0
for _ in range(N_PLACEBO):
    if rng.choice(ra,size=nc,replace=False).mean()>=rt.mean(): sup+=1
pct=sup/N_PLACEBO
ra_y={a:g.loc[g["tom"],"ret"].mean() for a,g in ins.groupby(ins["fecha"].dt.year) if g["tom"].sum()>=5}
apos=sum(1 for v in ra_y.values() if v>0)
chk=[nc>=30, ventaja>0, pct<0.05, (bool(ra_y) and apos>=len(ra_y)/2)]
print(f"\n=== JUICIO (horizonte 1 dia) ===")
print(f"1) Casos: {nc} -> {'PASA' if chk[0] else 'FALLA'}")
print(f"2) Ventaja vs cualquier dia: {ventaja*100:+.4f}% -> {'PASA' if chk[1] else 'FALLA'}")
print(f"3) Placebo: {pct*100:.1f}% iguala/supera -> {'PASA' if chk[2] else 'FALLA'} (<5%)")
print(f"4) Anios positivos: {apos}/{len(ra_y)} -> {'PASA' if chk[3] else 'FALLA'}")
print(f"\nVEREDICTO: {sum(chk)}/4")
