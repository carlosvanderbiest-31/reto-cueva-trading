#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

"""
Barrido parametrico generico · Cueva de Trading TIS

ESTRATEGIAS INTEGRADAS
  ewmac   -- cruce de dos medias exponenciales (fast, slow)
             Parametros: fast, slow

ESTRATEGIA PERSONALIZADA
  Crea codigo/<idea>.py con esta funcion obligatoria:

    def generar_senales(df, **params):
        # df: DataFrame con columnas date, open, high, low, close, volume
        # params: cualquier parametro que definas (periodo, umbral, etc.)
        # Retorna: np.ndarray de len(df) con valores +1.0 (largo) o -1.0 (corto)
        ...
        return signals

  Ese archivo es todo lo que necesitas escribir. El barrido, los costes,
  las metricas TIS y el informe los calcula optimizar.py automaticamente.

USO

  EWMAC (integrado):
    python codigo/optimizar.py \\
      --csv datos/btcusdt_1d_binance.csv \\
      --tipo ewmac \\
      --fast-base 32 --slow-base 128

  Estrategia personalizada con rangos automaticos:
    python codigo/optimizar.py \\
      --csv datos/eurusd_1h.csv \\
      --tipo codigo/mi_rsi.py \\
      --base "periodo=14,umbral=70" \\
      --barrido "periodo=5:50:5,umbral=60:80:5"

  Guardar resultados:
    python codigo/optimizar.py ... --output resultados/btcusd_ewmac_sweep.json
"""

import argparse, importlib.util, itertools, json
from pathlib import Path

import numpy as np
import pandas as pd

# ── Constantes TIS ──────────────────────────────────────────────────────────────
TIS_PF         = 1.3
TIS_OPS        = 30
TIS_MAX_DD     = 20.0
TIS_PF_NO_BEST = 1.0
PLATEAU_MIN    = 3

COST_PER_RT    = 0.003      # 30 pb por ida y vuelta
FUNDING_LONG   = 0.000301   # paga el largo por dia
FUNDING_SHORT  = -0.000301  # cobra el corto por dia


# ── Carga de datos ───────────────────────────────────────────────────────────────
def load_csv(path: str, insample_pct: float = 0.7) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["fecha"])
    df = df.rename(columns={"fecha": "date"})
    df = df.sort_values("date").reset_index(drop=True)
    df = df.dropna(subset=["close"])
    if len(df) < 50:
        sys.exit(f"Error: CSV tiene menos de 50 velas ({path})")
    if insample_pct < 1.0:
        cutoff = max(50, int(len(df) * insample_pct))
        df = df.iloc[:cutoff].reset_index(drop=True)
        print(f"  In-sample: {len(df)} velas ({insample_pct*100:.0f}%): "
              f"{df['date'].iloc[0].date()} a {df['date'].iloc[-1].date()}")
    return df


# ── Metricas genericas (cualquier estrategia) ────────────────────────────────────
def calcular_metricas(signals: np.ndarray, df: pd.DataFrame,
                      capital: float = 5000.0) -> dict:
    """
    Calcula todas las metricas TIS a partir de un array de senales.
    signals: array de len(df) con valores +1.0 o -1.0.
    """
    close     = df["close"].values.astype(float)
    dates     = pd.DatetimeIndex(df["date"])
    price_ret = np.diff(close) / close[:-1]

    # La senal del bar t se aplica al retorno del bar t+1 (sin lookahead)
    sig_lag   = signals[:-1]
    pos_ret   = sig_lag * price_ret

    trade_chg = np.concatenate([[0], np.diff(sig_lag)])
    costs     = np.where(trade_chg != 0, COST_PER_RT, 0.0)
    funding   = np.where(sig_lag > 0, FUNDING_LONG, FUNDING_SHORT)
    net_ret   = pos_ret - costs - funding

    equity    = np.concatenate([[capital], capital * np.cumprod(1 + net_ret)])

    pos_r = net_ret[net_ret > 0]
    neg_r = net_ret[net_ret < 0]
    pf    = float(pos_r.sum() / abs(neg_r.sum())) if len(neg_r) > 0 else float("inf")

    if len(pos_r) > 0:
        best_i = int(np.argmax(net_ret))
        nr2    = np.delete(net_ret, best_i)
        p2, n2 = nr2[nr2 > 0], nr2[nr2 < 0]
        pf_nb  = float(p2.sum() / abs(n2.sum())) if len(n2) > 0 else float("inf")
    else:
        pf_nb = 0.0

    peak   = np.maximum.accumulate(equity)
    max_dd = float(abs(((equity - peak) / peak).min())) * 100

    ops    = int(np.sum(trade_chg != 0))
    years  = (dates[-1] - dates[0]).days / 365.25
    ops_yr = ops / max(years, 1e-6)

    # Retornos anuales
    df_tmp = pd.DataFrame({"date": dates[1:], "ret": net_ret})
    df_tmp["year"] = df_tmp["date"].dt.year
    annual = {int(yr): float((1 + g["ret"]).prod() - 1)
              for yr, g in df_tmp.groupby("year")}
    yrs_pos = sum(1 for v in annual.values() if v > 0) / max(len(annual), 1)

    passes = (pf >= TIS_PF and ops >= TIS_OPS
              and max_dd < TIS_MAX_DD and pf_nb > TIS_PF_NO_BEST)

    return {
        "pf": round(pf, 4),
        "pf_no_best": round(pf_nb, 4),
        "max_dd": round(max_dd, 2),
        "ops": ops,
        "ops_yr": round(ops_yr, 2),
        "years_positive": round(yrs_pos, 3),
        "annual_returns": annual,
        "passes": passes,
    }


# ── Estrategias integradas ────────────────────────────────────────────────────────
def _senales_ewmac(df: pd.DataFrame, fast: int, slow: int, **_) -> np.ndarray:
    close = pd.Series(df["close"].values.astype(float))
    ewm_f = close.ewm(span=fast, adjust=False).mean().values
    ewm_s = close.ewm(span=slow, adjust=False).mean().values
    return np.where(ewm_f > ewm_s, 1.0, -1.0)


ESTRATEGIAS_INTEGRADAS = {
    "ewmac": _senales_ewmac,
}


# ── Carga de estrategia personalizada ────────────────────────────────────────────
def cargar_estrategia(tipo: str):
    """
    Retorna la funcion generar_senales(df, **params).
    tipo puede ser 'ewmac' (integrado) o la ruta a un .py con esa funcion.
    """
    if tipo in ESTRATEGIAS_INTEGRADAS:
        return ESTRATEGIAS_INTEGRADAS[tipo]

    path = Path(tipo)
    if not path.exists():
        sys.exit(f"Error: no existe '{tipo}'. Debe ser 'ewmac' o la ruta a un .py con generar_senales().")

    spec   = importlib.util.spec_from_file_location("estrategia_custom", path)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    if not hasattr(modulo, "generar_senales"):
        sys.exit(
            f"Error: '{tipo}' no tiene la funcion generar_senales(df, **params).\n"
            "Agrega esta funcion al archivo y vuelve a intentarlo."
        )
    return modulo.generar_senales


# ── Parseo de parametros CLI ──────────────────────────────────────────────────────
def _parsear_base(s: str) -> dict:
    """'fast=32,slow=128' -> {'fast': 32, 'slow': 128}"""
    result = {}
    for par in s.split(","):
        k, v = par.strip().split("=")
        result[k.strip()] = float(v.strip())
    return result


def _parsear_barrido(s: str) -> dict:
    """
    'fast=16:64:8,slow=64:256:32'
    -> {'fast': {'start':16,'end':64,'step':8}, 'slow': {'start':64,'end':256,'step':32}}
    """
    result = {}
    for par in s.split(","):
        name, rng = par.strip().split("=")
        parts = [float(x) for x in rng.strip().split(":")]
        result[name.strip()] = {
            "start": parts[0],
            "end":   parts[1],
            "step":  parts[2] if len(parts) > 2 else max(1, (parts[1] - parts[0]) / 10),
        }
    return result


def _derivar_rango(valor_base: float, pct_min: float = 0.5, pct_max: float = 2.0,
                   n_pasos: int = 7) -> dict:
    """Genera un rango automatico: [base*0.5, base*2] en ~7 pasos."""
    start = max(1, int(valor_base * pct_min))
    end   = int(valor_base * pct_max)
    step  = max(1, int((end - start) / (n_pasos - 1)))
    return {"start": start, "end": end, "step": step}


def _derivar_barrido_ewmac(fast_base: int, slow_base: int) -> dict:
    """Rango automatico para EWMAC: fast y slow."""
    return {
        "fast": _derivar_rango(fast_base),
        "slow": _derivar_rango(slow_base),
    }


# ── Motor de barrido generico ─────────────────────────────────────────────────────
def correr_barrido(df: pd.DataFrame, fn_senales, param_grid: dict,
                   capital: float = 5000.0) -> dict:
    """
    fn_senales(df, **params) -> signals array
    param_grid: {'param1': {'start':N,'end':M,'step':S}, ...}
    """
    # Pre-calcular EWMs si la estrategia es EWMAC (optimizacion de cache)
    usar_cache_ewm = (fn_senales in ESTRATEGIAS_INTEGRADAS.values()
                      and fn_senales == _senales_ewmac)
    ewm_cache: dict = {}

    if usar_cache_ewm:
        close_s = pd.Series(df["close"].values.astype(float))
        all_spans = set()
        for pname, prng in param_grid.items():
            for v in range(int(prng["start"]), int(prng["end"]) + 1, int(prng["step"])):
                all_spans.add(v)
        for span in all_spans:
            ewm_cache[span] = close_s.ewm(span=span, adjust=False).mean().values

    # Generar todas las combinaciones de parametros
    keys   = list(param_grid.keys())
    ranges = [list(range(int(pg["start"]), int(pg["end"]) + 1, int(pg["step"])))
              for pg in param_grid.values()]
    combos = list(itertools.product(*ranges))

    resultados = []
    omitidas   = 0

    for combo in combos:
        params = dict(zip(keys, combo))

        # Regla de validez para EWMAC: slow debe ser al menos el doble del fast
        if usar_cache_ewm:
            f, s = params.get("fast"), params.get("slow")
            if f and s and s <= f * 2:
                omitidas += 1
                continue
            # Usar cache
            ewm_f = ewm_cache.get(f)
            ewm_s = ewm_cache.get(s)
            if ewm_f is None or ewm_s is None:
                omitidas += 1
                continue
            signals = np.where(ewm_f > ewm_s, 1.0, -1.0)
        else:
            try:
                signals = fn_senales(df, **params)
            except Exception as e:
                omitidas += 1
                continue

        metricas = calcular_metricas(signals, df, capital)
        metricas.update(params)
        metricas.pop("annual_returns", None)  # no incluir en grid para no inflar JSON
        resultados.append(metricas)

    plateau     = [r for r in resultados if r["passes"]]
    best        = max(resultados, key=lambda r: r["pf"]) if resultados else None
    plateau_ord = sorted(plateau, key=lambda r: -r["pf"])

    return {
        "combos_tested":  len(resultados),
        "combos_skipped": omitidas,
        "results":        resultados,
        "plateau_combos": plateau_ord,
        "plateau_size":   len(plateau),
        "is_robust":      len(plateau) >= PLATEAU_MIN,
        "best_pf_combo":  best,
        "param_names":    keys,
    }


# ── Informe en texto ──────────────────────────────────────────────────────────────
def imprimir_informe(sw: dict, base_params: dict = None):
    sep = "-" * 60
    print(f"\n{sep}")
    print("BARRIDO PARAMETRICO TIS")
    print(f"Combinaciones probadas: {sw['combos_tested']}  |  Omitidas: {sw['combos_skipped']}")
    print(sep)

    plateau = sw["plateau_combos"]
    psize   = sw["plateau_size"]
    keys    = sw["param_names"]

    if psize == 0:
        print("MESETA: ninguna combinacion pasa 4/4 TIS")
        print("-> Estrategia NO es robusta en ningun parametro.")
    elif psize < PLATEAU_MIN:
        print(f"MESETA: {psize} combo(s) pasan 4/4  --  MARGINAL (necesita >={PLATEAU_MIN})")
        print("-> Funciona, pero solo con parametros muy especificos. Sospechoso.")
    else:
        print(f"MESETA: {psize} combinaciones pasan 4/4  --  ROBUSTA [OK]")
        print("-> La ventaja no depende de los parametros exactos.")

    print()
    if plateau:
        header_params = "  ".join(f"{k:>8}" for k in keys)
        print(f"  {header_params}  {'PF':>6}  {'DD%':>7}  {'ops/yr':>7}  {'PF_nb':>6}")
        for r in plateau[:20]:
            row_params = "  ".join(f"{r[k]:>8}" for k in keys)
            marker = ""
            if base_params and all(r.get(k) == base_params.get(k) for k in keys):
                marker = " <-- BASE"
            print(f"  {row_params}  {r['pf']:>6.3f}  {r['max_dd']:>6.1f}%  {r['ops_yr']:>7.1f}  "
                  f"{r['pf_no_best']:>6.3f}{marker}")

    best = sw["best_pf_combo"]
    if best:
        params_str = "  ".join(f"{k}={best[k]}" for k in keys)
        print(f"\nMejor PF: {params_str}  PF={best['pf']:.3f}  DD={best['max_dd']:.1f}%")
        if not best["passes"]:
            print("  (no pasa 4/4)")

    print(sep + "\n")


# ── CLI ───────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(
        description="Barrido parametrico para cualquier estrategia TIS"
    )
    p.add_argument("--csv",           required=True,
                   help="CSV curado en datos/")
    p.add_argument("--tipo",          default="ewmac",
                   help="'ewmac' (integrado) o ruta a codigo/<idea>.py con generar_senales()")
    # EWMAC: atajos para compatibilidad hacia atras
    p.add_argument("--fast-base",     type=int,   default=None)
    p.add_argument("--slow-base",     type=int,   default=None)
    p.add_argument("--fast-range",    default=None,
                   help="fast start,end,step  (ej: 8,64,8)")
    p.add_argument("--slow-range",    default=None,
                   help="slow start,end,step  (ej: 32,256,32)")
    # Interfaz generica
    p.add_argument("--base",          default=None,
                   help="Valores base: 'periodo=14,umbral=70'")
    p.add_argument("--barrido",       default=None,
                   help="Rangos: 'periodo=5:50:5,umbral=60:80:5'")
    # Comun
    p.add_argument("--insample-pct",  type=float, default=0.7)
    p.add_argument("--capital",       type=float, default=5000.0)
    p.add_argument("--output",        default=None,
                   help="JSON de salida (ej: resultados/btcusd_ewmac_sweep.json)")
    args = p.parse_args()

    # 1. Cargar estrategia
    fn = cargar_estrategia(args.tipo)

    # 2. Construir el param_grid
    if args.barrido:
        param_grid = _parsear_barrido(args.barrido)
    elif args.tipo == "ewmac" or fn == _senales_ewmac:
        # Atajos EWMAC
        if args.fast_range or args.slow_range:
            def _pr(s):
                parts = [int(x) for x in s.split(",")]
                return {"start": parts[0], "end": parts[1],
                        "step": parts[2] if len(parts) > 2 else max(1, (parts[1]-parts[0])//10)}
            fast_rng = _pr(args.fast_range) if args.fast_range else _derivar_rango(args.fast_base or 32)
            slow_rng = _pr(args.slow_range) if args.slow_range else _derivar_rango(args.slow_base or 128)
        else:
            fast_rng = _derivar_rango(args.fast_base or 32)
            slow_rng = _derivar_rango(args.slow_base or 128)
        param_grid = {"fast": fast_rng, "slow": slow_rng}
    elif args.base:
        base = _parsear_base(args.base)
        param_grid = {k: _derivar_rango(v) for k, v in base.items()}
    else:
        sys.exit("Especifica --barrido 'param=start:end:step,...' para estrategias no-EWMAC.")

    # Mostrar configuracion
    print(f"Tipo: {args.tipo}")
    for pname, prng in param_grid.items():
        print(f"  {pname}: {int(prng['start'])} -> {int(prng['end'])}  paso {int(prng['step'])}")
    print(f"In-sample: primero {int(args.insample_pct*100)}% del CSV")

    # 3. Cargar datos
    df = load_csv(args.csv, args.insample_pct)

    # 4. Correr barrido
    base_params = None
    if args.fast_base and args.slow_base:
        base_params = {"fast": args.fast_base, "slow": args.slow_base}
    elif args.base:
        base_params = _parsear_base(args.base)

    sw = correr_barrido(df, fn, param_grid, args.capital)
    sw["csv"] = args.csv
    sw["tipo"] = args.tipo

    # 5. Informe
    imprimir_informe(sw, base_params)

    # 6. Guardar
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        exportar = {k: v for k, v in sw.items() if k != "results"}
        exportar["results"] = sw["results"]
        with open(out, "w", encoding="utf-8") as f:
            json.dump(exportar, f, ensure_ascii=False, indent=2, default=str)
        print(f"Guardado en: {args.output}")


if __name__ == "__main__":
    main()
