# Fase 04 - Ruptura 30 velas 4h + filtros BCD (H2, H4, H6, H7), datos gratis.
# Mismo motor que btcusdt_ruptura30.py; cada filtro corre en su ventana, 70/30, veredicto FUERA DE MUESTRA.
import numpy as np, pandas as pd

VENTANA, ATR_N, MULT_STOP, RR, MAX_VELAS = 30, 14, 2.0, 2.0, 30
RIESGO, COSTE_LADO, CUENTA0 = 0.01, 0.001, 10000.0

df = pd.read_csv("datos/BTCUSDT_4h.csv", parse_dates=["time"]).sort_values("time").reset_index(drop=True)
df["t"] = df["time"].dt.tz_localize(None)
o,h,l,c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
n=len(df)
max_prev = pd.Series(h).rolling(VENTANA).max().shift(1).values
pc=pd.Series(c).shift(1)
tr=np.maximum(h-l, np.maximum((pd.Series(h)-pc).abs(),(pd.Series(l)-pc).abs()))
atr=tr.rolling(ATR_N).mean().values

def cargar(path, col):
    s=pd.read_csv(path, parse_dates=["fecha"]).sort_values("fecha")
    return s

def asof_lag(serie, col, lag_dias=1):
    # valor "conocido" con retraso de lag_dias: disponible a partir de fecha+lag
    s=serie.copy(); s["tdisp"]=s["fecha"]+pd.Timedelta(days=lag_dias)
    m=pd.merge_asof(df[["t"]], s[["tdisp",col]].rename(columns={"tdisp":"t"}), on="t", direction="backward")
    return m[col].values

# ---- construir filtros por vela ----
fng=cargar("datos/btc_fng.csv","fng");      fng_v=asof_lag(fng,"fng")
mv =cargar("datos/btc_mvrvz.csv","mvrvz");   mv_v =asof_lag(mv,"mvrvz")
pr =cargar("datos/btc_premium.csv","premium"); pr_v=asof_lag(pr,"premium")
etf=cargar("datos/btc_etfflow.csv","flujo")
etf["pos5"]=(etf["flujo"]>0).rolling(5).sum(); etf_v=asof_lag(etf,"pos5")
fund=cargar("datos/btc_funding.csv","funding")  # intradia, sin lag
fund_v=pd.merge_asof(df[["t"]], fund.rename(columns={"fecha":"t"}), on="t", direction="backward")["funding"].values

def primera_valida(arr):
    idx=np.where(~pd.isna(arr))[0]
    return idx[0] if len(idx) else n

def simular(ini, fin, permitido):
    cuenta=CUENTA0; equity=[]; cierres=[CUENTA0]; ops=[]; t=ini
    while t<fin-1:
        if not (c[t]>max_prev[t]) or np.isnan(atr[t]) or atr[t]<=0 or not permitido[t]:
            equity.append(cuenta); t+=1; continue
        entrada=o[t+1]; rp=MULT_STOP*atr[t]; stop=entrada-rp; obj=entrada+RR*rp
        if entrada<=stop: equity.append(cuenta); t+=1; continue
        rm=RIESGO*cuenta; u=rm/(entrada-stop); ce=COSTE_LADO*u*entrada
        k=t+1; sal=None
        while k<fin:
            equity.append(cuenta+u*(c[k]-entrada)-ce)
            if l[k]<=stop: sal=stop; break
            if h[k]>=obj: sal=obj; break
            if (k-(t+1))>=MAX_VELAS: sal=c[k]; break
            k+=1
        if sal is None: sal=c[fin-1]; k=fin-1
        pnl=u*(sal-entrada)-ce-COSTE_LADO*u*sal; cuenta+=pnl; cierres.append(cuenta)
        ops.append({"fecha":df["t"].iloc[t+1],"r":pnl/rm,"pnl":pnl}); t=k+1
    return cuenta, pd.DataFrame(ops), np.array(equity), np.array(cierres)

def metr(ops, eq, ci):
    r=ops["pnl"].values
    if len(r)==0: return 0,0,0,0,0
    g=r[r>0].sum(); p=-r[r<0].sum(); fb=g/p if p>0 else float("inf")
    rr=np.delete(r,np.argmax(r)) if len(r)>1 else r
    g2=rr[rr>0].sum(); p2=-rr[rr<0].sum(); fbs=g2/p2 if p2>0 else (float("inf") if g2>0 else 0)
    dd=((eq-np.maximum.accumulate(eq))/np.maximum.accumulate(eq)).min()*100 if len(eq) else 0
    return fb,fbs,len(r),dd,cuenta_na(ci)
def cuenta_na(ci): return ((ci-np.maximum.accumulate(ci))/np.maximum.accumulate(ci)).min()*100

HIPOTESIS={
 "H2 F&G<80 + MVRV-Z<7": ((fng_v<80)&(mv_v<7), max(primera_valida(mv_v),primera_valida(fng_v))),
 "H4 ETF +en >=3 de 5":  (etf_v>=3,            primera_valida(etf_v)),
 "H6 funding < P90":      (None,                primera_valida(fund_v)),  # umbral se fija con dentro-muestra
 "H7 Coinbase premium>0": (pr_v>0,              primera_valida(pr_v)),
}

for nombre,(filtro,ini0) in HIPOTESIS.items():
    ini=max(ini0, VENTANA+ATR_N)
    corte=ini+int((n-ini)*0.70)
    if nombre.startswith("H6"):
        # umbral P90 del funding en el tramo dentro de muestra
        p90=np.nanpercentile(fund_v[ini:corte],90)
        filtro=fund_v<p90
    permit=np.where(pd.isna(filtro), False, filtro)
    res={}
    for tr_n,(a,b) in {"DENTRO":(ini,corte),"FUERA":(corte,n)}.items():
        cu,ops,eq,ci=simular(a,b,permit); res[tr_n]=(cu,ops,eq,ci)
    print(f"\n########## {nombre} ##########")
    print(f"Ventana: {df['t'].iloc[ini].date()} -> {df['t'].iloc[-1].date()} | corte 70/30: {df['t'].iloc[corte].date()}")
    for tr_n in ("DENTRO","FUERA"):
        cu,ops,eq,ci=res[tr_n]; fb,fbs,no,dd,ddo=metr(ops,eq,ci)
        print(f"  {tr_n}: ops {no:>3} | FB {fb:.2f} | FB sin mejor {fbs:.2f} | caida v/v {dd:.1f}% | cuenta {cu:.0f}")
    cu,ops,eq,ci=res["FUERA"]; fb,fbs,no,dd,ddo=metr(ops,eq,ci)
    chk=[fb>=1.3, no>=30, abs(dd)<20, fbs>1]
    print(f"  VEREDICTO FUERA: {sum(chk)}/4  [FB>=1.3:{'ok' if chk[0] else 'NO'} | ops>=30:{'ok' if chk[1] else 'NO'} | dd<20:{'ok' if chk[2] else 'NO'} | FBsinmejor>1:{'ok' if chk[3] else 'NO'}]")
