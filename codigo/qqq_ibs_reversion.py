# Fase 04 - QQQ diario, reversion por IBS. Regla fase 03 sin cambios.
# Entrada: IBS<0.2 y close>MA200 -> open dia siguiente. Salida: close>high de ayer, o 5 dias. Stop: min de 10 dias.
import numpy as np, pandas as pd
RUTA="datos/qqq_1d_yahoo.csv"
IBS_UMBRAL, MA_N, STOP_N, MAX_DIAS = 0.20, 200, 10, 5
RIESGO, COSTE_LADO, CUENTA0 = 0.01, 0.0005, 10000.0

df=pd.read_csv(RUTA, parse_dates=["fecha"]).sort_values("fecha").reset_index(drop=True)
o,h,l,c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
n=len(df)
rango=(h-l); ibs=np.where(rango>0,(c-l)/rango,0.5)
ma=pd.Series(c).rolling(MA_N).mean().values
min10=pd.Series(l).rolling(STOP_N).min().values
senal=(ibs<IBS_UMBRAL)&(c>ma)
corte=int(n*0.70)

def simular(ini,fin):
    cuenta=CUENTA0; eq=[]; ci=[CUENTA0]; ops=[]; t=ini
    while t<fin-1:
        if not senal[t] or np.isnan(ma[t]) or np.isnan(min10[t]):
            eq.append(cuenta); t+=1; continue
        entrada=o[t+1]; stop=min10[t]
        if entrada<=stop: eq.append(cuenta); t+=1; continue
        rm=RIESGO*cuenta; u=rm/(entrada-stop); ce=COSTE_LADO*u*entrada
        k=t+1; sal=None
        while k<fin:
            eq.append(cuenta+u*(c[k]-entrada)-ce)
            if l[k]<=stop: sal=stop; break
            if c[k]>h[k-1]: sal=c[k]; break
            if (k-(t+1))>=MAX_DIAS: sal=c[k]; break
            k+=1
        if sal is None: sal=c[fin-1]; k=fin-1
        pnl=u*(sal-entrada)-ce-COSTE_LADO*u*sal; cuenta+=pnl; ci.append(cuenta)
        ops.append({"fecha":df["fecha"].iloc[t+1],"r":pnl/rm,"pnl":pnl}); t=k+1
    return cuenta, pd.DataFrame(ops), np.array(eq), np.array(ci)

def metr(ops,eq,ci):
    r=ops["pnl"].values
    if len(r)==0: return 0,0,0,0
    g=r[r>0].sum(); p=-r[r<0].sum(); fb=g/p if p>0 else float("inf")
    rr=np.delete(r,np.argmax(r)) if len(r)>1 else r
    g2=rr[rr>0].sum(); p2=-rr[rr<0].sum(); fbs=g2/p2 if p2>0 else (float("inf") if g2>0 else 0)
    dd=((eq-np.maximum.accumulate(eq))/np.maximum.accumulate(eq)).min()*100 if len(eq) else 0
    return fb,fbs,len(r),dd

res={}
for nm,(a,b) in {"DENTRO":(MA_N,corte),"FUERA":(corte,n)}.items():
    cu,ops,eq,ci=simular(a,b); res[nm]=(cu,ops,eq,ci); fb,fbs,no,dd=metr(ops,eq,ci)
    print(f"{nm}: {df['fecha'].iloc[a].date()}->{df['fecha'].iloc[b-1].date()} | ops {no} | FB {fb:.2f} | FB sin mejor {fbs:.2f} | caida v/v {dd:.1f}% | cuenta {cu:.0f}")
# guardar
pd.concat([res['DENTRO'][1].assign(tramo='DM'),res['FUERA'][1].assign(tramo='FM')]).to_csv('resultados/qqq_ibs_reversion_operaciones.csv',index=False)
cu,ops,eq,ci=res['FUERA']; fb,fbs,no,dd=metr(ops,eq,ci)
chk=[fb>=1.3,no>=30,abs(dd)<20,fbs>1]
print(f"\nVEREDICTO FUERA: {sum(chk)}/4 [FB>=1.3:{'ok' if chk[0] else 'NO'} | ops>=30:{'ok' if chk[1] else 'NO'} | dd<20:{'ok' if chk[2] else 'NO'} | FBsinmejor>1:{'ok' if chk[3] else 'NO'}]")
