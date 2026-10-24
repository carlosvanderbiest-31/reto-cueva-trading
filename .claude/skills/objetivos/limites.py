"""Tus límites en números · skill objetivos (cueva TIS).

Traduce el plan del trader (riesgo por operación, caída máxima, frecuencia, reglas de fondeo)
a lo que va a vivir, con una simulación de Monte Carlo (muchas secuencias de operaciones al azar).

Uso:
  python .claude/skills/objetivos/limites.py --riesgo 1 --caida 15 --ops-mes 20 \
      --operaciones resultados/<idea>_operaciones.csv
  python .claude/skills/objetivos/limites.py --riesgo 1 --caida 15 --ops-mes 20 \
      --acierto 45 --ratio 1.5          # sin backtest: estimación con supuestos
  Fondeo (opcional): --diario 5 --total 10 --ops-dia 3

--operaciones: CSV con una columna de resultado por operación en R (múltiplos del riesgo) o en
dinero (columna «r», «resultado», «profit» o «pnl»; si es dinero se pasa a R con la pérdida media).
Solo usa números: no necesita ni guarda datos de la cuenta.
"""
import argparse, builtins, csv, re, random, statistics as st, sys

def print(*a):  # decimales con coma, como en español
    builtins.print(*(re.sub(r'(\d)\.(\d)', r'\1,\2', str(x)) for x in a))

def leer_r(ruta):
    with open(ruta, newline='', encoding='utf-8-sig') as f:
        filas = list(csv.DictReader(f))
    if not filas:
        sys.exit('El CSV de operaciones está vacío.')
    cols = {c.lower().strip(): c for c in filas[0].keys()}
    for nombre in ('r', 'resultado_r', 'resultado', 'profit', 'pnl', 'beneficio'):
        if nombre in cols:
            col = cols[nombre]; break
    else:
        sys.exit('No encontré la columna de resultado (r, resultado, profit o pnl).')
    vals = []
    for fila in filas:
        t = (fila[col] or '').replace(',', '.').strip()
        if t:
            vals.append(float(t))
    if col.lower() != 'r' and col.lower() != 'resultado_r':
        perd = [v for v in vals if v < 0]
        if not perd:
            sys.exit('No hay operaciones perdedoras: no puedo medir el riesgo en R.')
        unidad = -st.mean(perd)          # supuesto: la pérdida media ≈ 1 R
        vals = [v / unidad for v in vals]
    return vals

def racha_max(seq):
    m = c = 0
    for v in seq:
        c = c + 1 if v < 0 else 0
        m = max(m, c)
    return m

def pct(x, p):
    x = sorted(x); return x[min(len(x) - 1, int(p / 100 * len(x)))]

def main():
    a = argparse.ArgumentParser()
    a.add_argument('--riesgo', type=float, required=True, help='% de la cuenta por operación')
    a.add_argument('--caida', type=float, required=True, help='caída máxima que aguanta, %')
    a.add_argument('--ops-mes', type=float, required=True, help='operaciones al mes')
    a.add_argument('--meses', type=int, default=12)
    a.add_argument('--operaciones', help='CSV de operaciones del backtest')
    a.add_argument('--acierto', type=float, help='% de ganadoras (sin backtest)')
    a.add_argument('--ratio', type=float, help='ganancia media / pérdida media (sin backtest)')
    a.add_argument('--diario', type=float, help='fondeo: pérdida máxima diaria, %')
    a.add_argument('--total', type=float, help='fondeo: pérdida máxima total, %')
    a.add_argument('--ops-dia', type=int, default=1, help='fondeo: operaciones máximas por día')
    a.add_argument('--sims', type=int, default=10000)
    o = a.parse_args()
    random.seed(42)

    if o.operaciones:
        R = leer_r(o.operaciones); fuente = f'backtest ({len(R)} operaciones de {o.operaciones})'
    elif o.acierto is not None and o.ratio is not None:
        p = o.acierto / 100
        R = None; fuente = f'ESTIMACIÓN con supuestos: {o.acierto:.0f} % de acierto, ratio {o.ratio}'
    else:
        sys.exit('Falta --operaciones o el par --acierto y --ratio.')

    n = max(1, round(o.ops_mes * o.meses))
    rachas, caidas, toca_caida, toca_total = [], [], 0, 0
    for _ in range(o.sims):
        seq = [random.choice(R) for _ in range(n)] if R else \
              [o.ratio if random.random() < p else -1.0 for _ in range(n)]
        eq = pico = 100.0; peor = 0.0
        for r in seq:
            eq *= 1 + r * o.riesgo / 100
            pico = max(pico, eq); peor = max(peor, (pico - eq) / pico * 100)
        rachas.append(racha_max(seq)); caidas.append(peor)
        toca_caida += peor >= o.caida
        if o.total: toca_total += peor >= o.total

    perdidas_hasta_caida = 0; eq = 100.0
    while (100 - eq) < o.caida:
        eq *= 1 - o.riesgo / 100; perdidas_hasta_caida += 1

    print(f'# Tus límites en números\nFuente: {fuente}')
    print(f'Supuestos: {o.riesgo} % por operación, {o.ops_mes:g} operaciones al mes, {o.meses} meses '
          f'({n} operaciones), {o.sims} simulaciones, semilla 42.\n')
    print(f'- Pérdidas seguidas hasta tu caída máxima del {o.caida:g} %: {perdidas_hasta_caida}')
    print(f'- Peor racha de pérdidas seguidas en {o.meses} meses: la mitad de las veces {pct(rachas,50)} o más; '
          f'1 de cada 20 veces, {pct(rachas,95)} o más')
    print(f'- Peor caída en {o.meses} meses: típica {pct(caidas,50):.1f} %; 1 de cada 20 veces {pct(caidas,95):.1f} % o más')
    print(f'- Probabilidad de tocar tu caída máxima del {o.caida:g} % en {o.meses} meses: {toca_caida/o.sims*100:.0f} %')
    if o.total:
        print(f'- Fondeo: probabilidad de tocar la pérdida máxima total del {o.total:g} %: {toca_total/o.sims*100:.0f} %')
    if o.diario:
        k = 0; eq = 100.0
        while (100 - eq) < o.diario:
            eq *= 1 - o.riesgo / 100; k += 1
        aviso = 'puedes tocarlo en un solo día' if k <= o.ops_dia else 'no lo tocas en un día con tu límite de operaciones'
        print(f'- Fondeo: pérdidas seguidas hasta el límite diario del {o.diario:g} %: {k} → con {o.ops_dia} '
              f'operaciones al día, {aviso}')
    print('\nEsto describe el riesgo que eliges, no promete resultados. Con menos de 30 operaciones de '
          'backtest, o sin backtest, es solo una estimación.')

if __name__ == '__main__':
    main()
