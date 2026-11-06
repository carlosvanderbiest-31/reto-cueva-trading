# FICHA · QQQ diario · reversión por IBS (idea #1 del Banco de Ideas)
Regla: Compro QQQ cuando el cierre queda en el 20% bajo del rango del día (IBS<0,2) estando sobre la media de 200 días. Salgo cuando el cierre supera el máximo del día anterior, o a los 5 días. Stop: 2×ATR(14). Horario: diario.
Por qué funcionaría: sobrerreacción de corto plazo — quien vende forzado cerca del mínimo del día paga liquidez a quien compra; en tendencia alcista el precio rebota (familia Reversión a la media, Banco de Ideas VIP).

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: hipotesis-trading
Qué se hizo: idea #1 del banco (reversión en índices, variante IBS) concretada en QQQ diario.
Resultado: entrada IBS<0,2 y close>MA200; salida close>máximo de ayer o 5 días; stop 2×ATR.
Supuestos: riesgo 1% = $10; costes 0,05%/lado (ETF índice líquido).
Veredicto: APRUEBA
Siguiente paso: medir si el rebote es ventaja o ruido (fase 02).

## Fase 02 · AED · CRITERIO + DATOS
Agente / skill: aed
Qué se hizo: retorno forward tras IBS<0,2 y close>MA200 vs cualquier día, 4 condiciones, 70% más antiguo de qqq_1d_yahoo.csv (2000→2018). Código: codigo/qqq_ibs_reversion_aed.py.
Resultado: H=3 días → señal +0,204% vs base -0,007% = +0,211%. Casos 529. Placebo 3,7%. Años positivos 10/15. Contexto H=1 +0,10%, H=5 +0,34%.
Supuestos: costes 0,05%/lado; horizonte 3 días declarado antes de medir.
Veredicto: APRUEBA (4/4)
Siguiente paso: escribir reglas (fase 03) y backtest (fase 04).

## Fase 03 · Reglas · MOTOR
Agente / skill: reglas (manual)
Qué se hizo: pseudocódigo sin look-ahead. Primer intento con stop=mínimo de 10 días dio sizing degenerado (stop pegado a la entrada → apalancamiento absurdo → cuenta negativa); se corrigió el stop a 2×ATR ANTES de juzgar.
Resultado: pseudocódigo abajo.
Supuestos: entrada en el open del día siguiente; stop primero si coincide con la salida; una posición a la vez.
Veredicto: PENDIENTE (MOTOR; se juzga en fase 04)
Siguiente paso: backtest fuera de muestra.

## Fase 04 · Backtest · MOTOR
Agente / skill: validador-4de4
Qué se hizo: backtest 1% riesgo, costes 0,05%/lado, 70/30 sobre 2000→2026. Código: codigo/qqq_ibs_reversion_atr.py (stop 2×ATR). El stop de 10 días original (codigo/qqq_ibs_reversion.py) queda como evidencia del defecto de sizing.
Resultado: DENTRO (2000→2018): 345 ops, FB 1,15, caída 5,6%. FUERA (2018→2026): 183 ops, FB 1,19, FB sin mejor 1,16, caída 7,9%.
Supuestos: stop 2×ATR (corrige el degenerado); costes 0,05%/lado.
Veredicto: NO APRUEBA (3/4 fuera de muestra: falla factor de beneficio ≥1,3, quedó en 1,19).
Siguiente paso: descartar (no afinar). La ventaja IBS es real pero modesta. Seguir con idea #2 del plan.

---
PSEUDOCÓDIGO · qqq_ibs_reversion
  IBS[t] = (close[t]-low[t]) / (high[t]-low[t])
  MA200[t] = media 200 de close ; ATR[t] = media 14 del True Range
  SI no hay posición Y IBS[t]<0,20 Y close[t]>MA200[t]:
      entrada = open[t+1] ; stop = entrada - 2*ATR[t]
      tamaño tal que pérdida al stop = 1% de la cuenta
  SI hay posición (desde t+1):
      SI low[k]<=stop: cerrar a stop
      SINO SI close[k]>high[k-1]: cerrar a close[k]      # reversión lograda
      SINO SI (k-(t+1))>=5: cerrar a close[k]            # salida por tiempo
  Costes: 0,05% por lado en entrada y salida.
