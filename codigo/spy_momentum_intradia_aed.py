# AED fase 02 - S&P 500 CFD, momentum intradia (Gao et al 2018)
# Trade la ultima media hora en la direccion de la primera media hora. Datos dukascopy M15, origen UTC+3.
import numpy as np, pandas as pd
COSTE_RT=2*0.0001; SEMILLA=42; N_PLACEBO=1000

d=pd.read_parquet('datos_limpios/dukascopy/M15/USA500IDXUSD.parquet').rename(columns={'datetime_servidor':'t'})
d['t']=pd.to_datetime(d['t']).dt.tz_localize('Etc/GMT-3').dt.tz_convert('US/Eastern')
d['dia']=d['t'].dt.date; d['hm']=d['t'].dt.strftime('%H:%M')

def bar(df,hm,col):
    s=df[df['hm']==hm]; return s.set_index('dia')[col]
o0930=bar(d,'09:30','open'); c0945=bar(d,'09:45','close')
o1530=bar(d,'15:30','open'); c1545=bar(d,'15:45','close')
P=pd.DataFrame({'o0930':o0930,'c0945':c0945,'o1530':o1530,'c1545':c1545}).dropna()
P['r_first']=P['c0945']/P['o0930']-1
P['r_last']=P['c1545']/P['o1530']-1
P['strat']=np.sign(P['r_first'])*P['r_last']
P=P[P['r_first']!=0]
P.index=pd.to_datetime(P.index); P=P.sort_index()

n=len(P); corte=int(n*0.70); ins=P.iloc[:corte]
print(f"Dias con datos completos: {n} | corte 70% en {P.index[corte].date()}")
print(f"In-sample: {ins.index[0].date()} -> {ins.index[-1].date()} ({len(ins)} dias)")

s=ins['strat'].values - COSTE_RT
nc=len(s); media=s.mean()
print(f"\nRetorno medio por dia (dir. primera 1/2h aplicada a ultima 1/2h, neto): {media*100:+.4f}%")
print(f"Aciertos de direccion: {(ins['strat']>0).mean()*100:.1f}%")
# placebo: signo al azar
rng=np.random.default_rng(SEMILLA); rl=ins['r_last'].values; sup=0
for _ in range(N_PLACEBO):
    signo=rng.choice([-1,1],size=nc)
    if (signo*rl-COSTE_RT).mean()>=media: sup+=1
pct=sup/N_PLACEBO
ins2=ins.copy(); ins2['anio']=ins2.index.year
ra={a:(g['strat'].mean()-COSTE_RT) for a,g in ins2.groupby('anio') if len(g)>=5}
apos=sum(1 for v in ra.values() if v>0)
chk=[nc>=30, media>0, pct<0.05, (bool(ra) and apos>=len(ra)/2)]
print(f"\n=== JUICIO (horizonte: ultima media hora) ===")
print(f"1) Casos: {nc} -> {'PASA' if chk[0] else 'FALLA'}")
print(f"2) Ventaja neta (>0): {media*100:+.4f}% -> {'PASA' if chk[1] else 'FALLA'}")
print(f"3) Placebo (signo al azar): {pct*100:.1f}% iguala/supera -> {'PASA' if chk[2] else 'FALLA'} (<5%)")
print(f"4) Anios positivos: {apos}/{len(ra)} -> {'PASA' if chk[3] else 'FALLA'}")
print(f"   por anio:", {a:round(v*100,3) for a,v in ra.items()})
print(f"\nVEREDICTO: {sum(chk)}/4")
