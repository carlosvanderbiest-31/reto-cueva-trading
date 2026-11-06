# FICHA · BTC ruptura del máximo de 30 velas (4h)
Regla: Compro BTCUSDT cuando el cierre de 4h supera el máximo de las 30 velas anteriores. Salgo cuando toco objetivo (2R), stop, o pasan 30 velas. Stop: 2×ATR(14). Horario: 24/7, velas de 4 horas.
Por qué funcionaría: el capital persigue al precio que rompe a nuevos máximos; es momentum. Prima de riesgo (no ineficiencia que se arbitre): persiste porque exige aguantar volatilidad y reversiones. Base de las hipótesis H2/H4/H6/H7 de BCD, sin el filtro externo que aún no tiene datos.

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: hipotesis-trading
Qué se hizo: se definió el comportamiento a explotar — ruptura de momentum en BTC tras nuevo máximo de 30 velas 4h.
Resultado: hipótesis concreta con entrada, stop (2×ATR) y objetivo (2R); mercado BTCUSDT Bitunix, 4h.
Supuestos: apalancamiento moderado (x3–x5) para respetar caída tolerable 20%; riesgo 1% = $10 por operación.
Veredicto: APRUEBA
Siguiente paso: medir si el comportamiento es ventaja o ruido (fase 02).

## Fase 02 · AED · CRITERIO + DATOS
Agente / skill: aed
Qué se hizo: medí el retorno forward tras la señal vs cualquier vela, con 4 condiciones TIS, sobre el 70% más antiguo de BTCUSDT_4h.csv (2017-08-17 → 2024-01-24). Código: codigo/btcusdt_ruptura30_aed.py.
Resultado: H=20 velas → señal +1,572% vs base +0,368% = +1,204% neto. Casos: 598. Placebo (1000 sorteos, semilla 42): 0,0% iguala/supera. Años positivos: 5/7. Contexto: H=1 +0,14%, H=5 +0,80%.
Supuestos: costes 0,1% por lado (0,2% round-trip) (supuesto). Horizonte 20 velas declarado antes de medir. Datos Binance; calidad no auditada con informe formal (supuesto APTA).
Veredicto: APRUEBA (4/4)
Siguiente paso: escribir la regla sin ambigüedad (fase 03).

## Fase 03 · Reglas · MOTOR
Agente / skill: reglas (manual del agente)
Qué se hizo: traduje la hipótesis a pseudocódigo paso a paso, sin look-ahead, listo para backtest.
Resultado: pseudocódigo completo abajo.
Supuestos: entrada en el open de la vela siguiente al cierre que confirma; si stop y objetivo caen en la misma vela, se asume que toca primero el stop (conservador); una sola posición a la vez; sin apalancamiento en el backtest (riesgo fijo 1% al stop, medida estándar TIS).
Veredicto: PENDIENTE (es MOTOR, no da veredicto; se juzga en fase 04)
Siguiente paso: fase 04, validador-4de4, sobre el 30% reservado (2024-01 → 2026) con costes.

---
PSEUDOCÓDIGO · btcusdt_ruptura30

PARÁMETROS:
  VENTANA   = 30        # velas para el máximo previo
  ATR_N     = 14        # velas para el ATR
  MULT_STOP = 2.0       # stop = 2 × ATR
  RR        = 2.0       # objetivo = 2 × riesgo
  MAX_VELAS = 30        # cierre por tiempo
  RIESGO    = 0.01      # 1% del capital al stop (medida estándar fase 04)
  COSTE_LADO = 0.001    # 0,1% por lado (supuesto)

DATOS: BTCUSDT velas 4h (open, high, low, close), orden cronológico.

CÁLCULO PREVIO (sin mirar el futuro):
  max_prev[t] = máximo de high[t-30 .. t-1]      # 30 velas ANTERIORES
  ATR[t]      = media móvil 14 del True Range hasta la vela t

LÓGICA, recorriendo vela a vela t:
  SI no hay posición abierta:
      SI close[t] > max_prev[t]:                  # ruptura confirmada al cierre
          entrada  = open[t+1]                    # entro en la vela siguiente
          riesgo_precio = MULT_STOP × ATR[t]
          stop     = entrada − riesgo_precio
          objetivo = entrada + RR × riesgo_precio
          vela_entrada = t+1
          abrir LARGO

  SI hay posición abierta (desde vela_entrada):
      SI low[t]  <= stop:        cerrar a stop        # pérdida (prioridad si coincide con objetivo)
      SINO SI high[t] >= objetivo: cerrar a objetivo  # ganancia 2R
      SINO SI (t − vela_entrada) >= MAX_VELAS: cerrar a close[t]   # salida por tiempo

COSTES: restar COSTE_LADO en la entrada y en la salida de cada operación.
TAMAÑO (fase 04): posición tal que la pérdida al stop = 1% del capital.

SUPUESTOS:
  - Entrada en el open siguiente al cierre que confirma (sin look-ahead).
  - Si stop y objetivo ocurren en la misma vela, gana el stop (conservador).
  - Una sola posición simultánea.
  - 24/7, sin filtro de horario (cripto).

## Fase 04 · Backtest · MOTOR
Agente / skill: validador-4de4
Qué se hizo: backtest de la regla tal cual, 1% riesgo fijo, costes 0,1%/lado, 70% dentro / 30% fuera de muestra. Código: codigo/btcusdt_ruptura30.py. Corte: 2024-01-24.
Resultado: DENTRO (2017→2024): 231 ops, FB 1,38, FB sin mejor 1,36, caída vela a vela 10,5% (4/4). FUERA (2024→2026): 104 ops, FB 0,96, FB sin mejor 0,93, caída vela a vela 14,2%, caída op por op 13,4%.
Supuestos: costes 0,1% por lado (supuesto); tamaño estándar TIS (1% al stop); sin apalancamiento en el backtest.
Veredicto: NO APRUEBA (2/4 fuera de muestra: falla factor de beneficio ≥1,3 y FB sin mejor op >1).
Siguiente paso: la regla se descarta; volver a la fase 01 con una idea NUEVA (no una variante de esta).
