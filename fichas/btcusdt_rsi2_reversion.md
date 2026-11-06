# FICHA · BTC diario · reversión por sobreventa (RSI2<5 sobre MA200)
Regla: Compro BTCUSDT cuando el RSI de 2 días cae bajo 5 estando el precio sobre su media de 200 días. Salgo cuando el cierre supera el máximo del día anterior. Stop: bajo el mínimo de los últimos 10 días. Horario: diario.
Por qué funcionaría: propuesta — un retroceso brusco en tendencia alcista atrae compradores y el precio rebota (reversión a la media).

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: hipotesis-trading
Qué se hizo: se definió el comportamiento — rebote tras sobreventa extrema en tendencia alcista, BTC diario.
Resultado: hipótesis concreta con entrada (RSI2<5 y close>MA200), salida (close>máximo de ayer) y stop (mínimo de 10 días).
Supuestos: riesgo 1% = $10; sin apalancamiento en el estudio.
Veredicto: APRUEBA
Siguiente paso: medir si el rebote es ventaja o ruido (fase 02).

## Fase 02 · AED · CRITERIO + DATOS
Agente / skill: aed
Qué se hizo: medí el retorno forward tras la señal vs cualquier día, 4 condiciones TIS, sobre el 70% más antiguo de btcusdt_1d_binance.csv (2017-08 → 2024-01). Código: codigo/btcusdt_rsi2_reversion_aed.py.
Resultado: H=5 días → señal +0,616% vs base +0,661% = -0,045% (sin ventaja). Casos: 216. Placebo: 51,5% iguala/supera. Años positivos: 3/6. Contexto: H=1 +0,10%, H=10 +0,13%.
Supuestos: costes 0,1%/lado; RSI(2) estilo Cutler; horizonte 5 días declarado antes de medir. Datos APTA CON AVISOS (5 saltos a revisar, probablemente reales).
Veredicto: NO APRUEBA (2/4: falla ventaja vs cualquier día y placebo; es ruido).
Siguiente paso: la regla se descarta; volver a la fase 01 con una idea nueva. No se hacen las fases 03-04 con esta regla.
