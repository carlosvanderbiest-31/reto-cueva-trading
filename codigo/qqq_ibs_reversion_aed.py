# AED fase 02 - QQQ diario, reversion por IBS (cierre en parte baja del rango sobre MA200)
import numpy as np, pandas as pd
RUTA="datos/qqq_1d_yahoo.csv"
IBS_UMBRAL, MA_N = 0.20, 200
HORIZONTES=[1,3,5]; H_JUICIO=3
COSTE_RT=2*0.0005; SEMILLA=42; N_PLACEBO=1000

df=pd.read_csv(RUTA, parse_dates=["fecha"]).sort_values("fecha").reset_index(drop=True)
n=len(df); corte=int(n*0.70); fecha_corte=df.loc[corte,"fecha"]
ins=df.iloc[:corte].reset_index(drop=True)
print(f"Velas totales: {n} | corte 70% en {fecha_corte.date()}")
print(f"In-sample: {ins['fecha'].iloc[0].date()} -> {ins['fecha'].iloc[-1].date()} ({len(ins)} velas)")

h_,l_,c=ins["high"].values, ins["low"].values, ins["close"].values
rango=(h_-l_); ibs=np.where(rango>0,(c-l_)/rango,0.5)
ma=pd.Series(c).rolling(MA_N).mean().values
senal=(ibs<IBS_UMBRAL)&(c>ma); senal[:MA_N]=False

def ret_fwd(h):
    r=np.full(len(c),np.nan); r[:-h]=c[h:]/c[:-h]-1.0; return r

print("\n--- Retornos forward (media, netos de coste) ---")
print(f"{'H':>4} | {'n_senal':>8} | {'media_senal':>12} | {'media_base':>11} | {'dif':>9}")
for h in HORIZONTES:
    r=ret_fwd(h); mask=senal&~np.isnan(r)
    rs_=r[mask]-COSTE_RT; rb=r[~np.isnan(r)]-COSTE_RT
    print(f"{h:>4} | {mask.sum():>8} | {rs_.mean():>12.5f} | {rb.mean():>11.5f} | {rs_.mean()-rb.mean():>9.5f}")

h=H_JUICIO; r=ret_fwd(h); mask=senal&~np.isnan(r)
rs_=r[mask]-COSTE_RT; base=r[~np.isnan(r)]-COSTE_RT; n_casos=int(mask.sum())
ventaja=rs_.mean()-base.mean()
rng=np.random.default_rng(SEMILLA); pool=r[~np.isnan(r)]; sup=0
for _ in range(N_PLACEBO):
    if (rng.choice(pool,size=n_casos,replace=False)-COSTE_RT).mean()>=rs_.mean(): sup+=1
pct=sup/N_PLACEBO
ins_s=ins.copy(); ins_s["r"]=r; ins_s["senal"]=senal; ins_s["anio"]=ins_s["fecha"].dt.year
ra={}
for a,gg in ins_s[ins_s["senal"]&~ins_s["r"].isna()].groupby("anio"):
    if len(gg)>=5: ra[a]=gg["r"].mean()-COSTE_RT
apos=sum(1 for v in ra.values() if v>0)
print(f"\n=== JUICIO H={h} dias ===")
print(f"1) Casos: {n_casos} -> {'PASA' if n_casos>=30 else 'FALLA'} (>=30)")
print(f"2) Ventaja vs cualquier dia: senal {rs_.mean()*100:.3f}% vs base {base.mean()*100:.3f}% = {ventaja*100:+.3f}% -> {'PASA' if ventaja>0 else 'FALLA'}")
print(f"3) Placebo: {pct*100:.1f}% iguala/supera -> {'PASA' if pct<0.05 else 'FALLA'} (<5%)")
print(f"4) Anios positivos: {apos}/{len(ra)} -> {'PASA' if ra and apos>=len(ra)/2 else 'FALLA'}")
print(f"\nVEREDICTO: {sum([n_casos>=30, ventaja>0, pct<0.05, (bool(ra) and apos>=len(ra)/2)])}/4")
