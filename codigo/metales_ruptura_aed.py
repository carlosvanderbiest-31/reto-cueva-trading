# AED fase 02 - Oro y plata, ruptura del maximo de 50 dias (tendencia)
import numpy as np, pandas as pd
VENTANA=50; HORIZONTES=[5,20,60]; H_JUICIO=20
COSTE_RT=2*0.0005; SEMILLA=42; N_PLACEBO=1000

def aed(simbolo):
    d=pd.read_parquet(f"datos_limpios/darwinex/D1/{simbolo}.parquet").rename(columns={"datetime_servidor":"fecha"})
    d["fecha"]=pd.to_datetime(d["fecha"]); d=d.sort_values("fecha").reset_index(drop=True)
    n=len(d); corte=int(n*0.70); ins=d.iloc[:corte].reset_index(drop=True)
    h=ins["high"].values; c=ins["close"].values
    max_prev=pd.Series(h).rolling(VENTANA).max().shift(1).values
    senal=c>max_prev; senal[:VENTANA]=False
    def rf(hh):
        r=np.full(len(c),np.nan); r[:-hh]=c[hh:]/c[:-hh]-1.0; return r
    print(f"\n==== {simbolo} ==== in-sample {ins['fecha'].iloc[0].date()}->{ins['fecha'].iloc[-1].date()} ({corte} velas)")
    print(f"{'H':>4} | {'n':>5} | {'senal':>10} | {'base':>10} | {'dif':>9}")
    for hh in HORIZONTES:
        r=rf(hh); m=senal&~np.isnan(r)
        print(f"{hh:>4} | {m.sum():>5} | {(r[m]-COSTE_RT).mean():>10.5f} | {(r[~np.isnan(r)]-COSTE_RT).mean():>10.5f} | {(r[m]-COSTE_RT).mean()-(r[~np.isnan(r)]-COSTE_RT).mean():>9.5f}")
    h=H_JUICIO; r=rf(h); m=senal&~np.isnan(r)
    rs=r[m]-COSTE_RT; base=r[~np.isnan(r)]-COSTE_RT; nc=int(m.sum()); vent=rs.mean()-base.mean()
    rng=np.random.default_rng(SEMILLA); pool=r[~np.isnan(r)]; sup=0
    for _ in range(N_PLACEBO):
        if (rng.choice(pool,size=nc,replace=False)-COSTE_RT).mean()>=rs.mean(): sup+=1
    pct=sup/N_PLACEBO
    ins2=ins.copy(); ins2["r"]=r; ins2["senal"]=senal; ins2["anio"]=ins2["fecha"].dt.year
    ra={a:(g["r"].mean()-COSTE_RT) for a,g in ins2[ins2["senal"]&~ins2["r"].isna()].groupby("anio") if len(g)>=5}
    apos=sum(1 for v in ra.values() if v>0)
    chk=[nc>=30, vent>0, pct<0.05, (bool(ra) and apos>=len(ra)/2)]
    print(f"JUICIO H={h}: casos {nc} ({'ok' if chk[0] else 'NO'}) | ventaja {vent*100:+.3f}% ({'ok' if chk[1] else 'NO'}) | placebo {pct*100:.1f}% ({'ok' if chk[2] else 'NO'}) | anios {apos}/{len(ra)} ({'ok' if chk[3] else 'NO'})")
    print(f"   -> {sum(chk)}/4")
    return sum(chk)

v1=aed("XAUUSD"); v2=aed("XAGUSD")
print(f"\nRESUMEN AED: oro {v1}/4 | plata {v2}/4")
