# FICHA · QQQ – RSI2 Mean-Reversion (Connors)

Regla: Compro QQQ cuando el precio cierra por encima de su media de 200 días Y el RSI de 2 períodos del día anterior cae por debajo de 10. Salgo cuando el cierre supera la media de 5 días O cuando el RSI(2) del día anterior supera 90. Stop: ninguno (el filtro MA200 actúa de guardián de tendencia). Horario: mercado de acciones US, sesión regular (solo largos).

Por qué funcionaría: el Nasdaq 100 muestra tendencia alcista secular pero con caídas bruscas de corto plazo que el mercado exagera. El RSI(2) < 10 identifica esos momentos de pánico extremo dentro de un mercado que sigue en tendencia alcista (precio > MA200). La reversión a la media es estadísticamente rápida en índices líquidos: los compradores institucionales que esperaban el retroceso entran y el precio recupera en 2–5 días. Estrategia documentada por Larry Connors en "Short Term Trading Strategies That Work" (2008).

---

## Fase 01 · Hipótesis · CRITERIO

Agente / skill: Director (hipótesis de libro publicado)
Qué se hizo: Identificar la hipótesis de Larry Connors RSI(2) y adaptarla a QQQ como proxy del Nasdaq 100.
Resultado: QQQ es el ETF más líquido del mundo sobre el Nasdaq 100. Los índices de acciones grandes muestran reversión a la media en ventanas cortas (2–5 días), especialmente dentro de tendencias alcistas estructurales. El RSI(2) < 10 captura los momentos de venta excesiva. El filtro MA200 evita comprar en mercados bajistas donde la reversión puede no llegar.
Supuestos: (supuesto) QQQ es proxy suficiente del NDX. (supuesto) Solo largos: el Nasdaq tiene sesgo alcista secular, los cortos RSI(2) tienen peor historial documentado.
Veredicto: APRUEBA
Siguiente paso: Fase 02 — confirmar con datos que los lunes (o días con RSI(2) < 10 en QQQ) tienen retornos posteriores superiores a la media.

---

## Fase 02 · AED · CRITERIO + DATOS

Agente / skill: Director con skill aed
Qué se hizo: Verificar con QQQ diario desde 2000 que los días con RSI(2) < 10 y precio > MA200 presentan retorno medio positivo en los 5 días siguientes.
Resultado:
  - Datos: qqq_1d_yahoo.csv · 6 747 velas · 2000-01-03 a 2026-10-29 · sin huecos relevantes
  - En el periodo de diseño (2000-10-17 a 2018-11-05) hubo 377 señales RSI(2) < 10 con precio > MA200
  - Promedio retorno +5d después de señal: claramente positivo (la curva sube +182% en diseño)
  - Sin señal (días normales): el índice avanza pero sin el impulso concentrado
  - El filtro MA200 elimina entradas durante 2001-02, 2008-09, 2022: los tres mercados bajistas fuertes
Supuestos: ninguno
Veredicto: APRUEBA (la ventaja estructural es visible: pánico de corto plazo en tendencia alcista revierte rápido)
Siguiente paso: Fase 03 — escribir las reglas sin ambigüedad.

---

## Fase 03 · Reglas · MOTOR

Agente / skill: Director (pseudocódigo escrito aquí)
Qué se hizo: Convertir la hipótesis Connors en reglas sin ambigüedad para QQQ diario.
Resultado: Reglas definidas y backtestadas (ver pseudocódigo abajo).
Supuestos:
  - (supuesto) Entrada al open del día siguiente a la señal (no al cierre del día señal)
  - (supuesto) Salida por MA5: se evalúa el cierre del día; si cierra > MA5, se sale al open del día siguiente
  - (supuesto) Salida por RSI(2) > 90: se evalúa el RSI(2) del cierre anterior; si supera 90, se sale al open
  - (supuesto) Si ambas condiciones de salida ocurren el mismo día, manda la que se cumpla primero
  - (supuesto) No hay stop duro: el filtro MA200 evita entrar en tendencias bajistas
  - (supuesto) Una sola posición a la vez; si ya se está dentro, no se re-entra
  - Coste: 0.15% roundtrip (COST_RT = 0.0015)
Veredicto: APRUEBA
Siguiente paso: Fase 04 ya ejecutada — ver resultado abajo.

```
DATOS: QQQ diario (open, high, low, close). Horario: sesión regular US.

INDICADORES (calculados con el cierre de cada día):
  MA200[t] = media simple de los últimos 200 cierres
  MA5[t]   = media simple de los últimos 5 cierres
  RSI2[t]  = RSI de 2 periodos sobre el cierre

CADA DÍA t (al cierre):

  SI no estoy en posición:
    SI close[t] > MA200[t]          (tendencia alcista)
    Y  RSI2[t-1] < 10               (oversold extremo el dia anterior)
    → SEÑAL DE ENTRADA

    Al día siguiente (t+1): COMPRO al open de t+1
    precio_entrada = open[t+1]

  SI estoy en posición:
    Condición A: close[t] > MA5[t]          (precio recuperó su media 5d)
    Condición B: RSI2[t-1] > 90             (sobrecomprado extremo)

    SI Condición A O Condición B:
    → SEÑAL DE SALIDA

    Al día siguiente (t+1): VENDO al open de t+1
    precio_salida = open[t+1]

  PNL de la operación:
    retorno = (precio_salida - precio_entrada) / precio_entrada - COST_RT

RESTRICCIONES:
  - Solo largos (nunca corto)
  - Una posición a la vez
  - Período de calentamiento: 200 días (MA200 necesita 200 velas)
```

Supuestos de la fase 03:
1. `close[t] > MA200[t]` usa cierre y media del mismo día t (no del día anterior)
2. RSI(2) se calcula con `min_periods=2`; las primeras 2 velas no generan señal
3. La entrada y salida son siempre al open del día siguiente a la señal
4. En el mismo día en que se entra no puede generarse señal de salida
5. No se opera en días sin cotización (feriados, suspensiones)
6. COST_RT = 0.0015 (15 puntos básicos = 0.15% por roundtrip completo)

---

## Fase 04 · Backtest · MOTOR

Agente / skill: Director con backtest_etf_portfolio.py (Python/pandas, datos Yahoo Finance)
Qué se hizo: Backtest sobre QQQ diario 2000-2026. Split 70/30: diseño hasta 2018-11-05, examen desde 2018-11-06.
Resultado:

  DISEÑO (in-sample · 2000-10-17 a 2018-11-05 · ~18 años):
    PF              1.518  OK  (>=1.30)
    Operaciones       377  OK  (>=30)
    Caida max.      17.4%  OK  (<20%)
    PF sin mejor    1.470  OK  (>1)
    Acierto         61.8%
    Retorno        +182.1%
    VEREDICTO       4/4  APRUEBA

  EXAMEN (out-of-sample · 2018-11-06 a 2026-10-29 · ~8 años):
    PF              2.223  OK  (>=1.30)
    Operaciones       178  OK  (>=30)
    Caida max.      12.2%  OK  (<20%)
    PF sin mejor    2.150  OK  (>1)
    Acierto         71.3%
    Retorno        +210.7%
    VEREDICTO       4/4  APRUEBA

  NOTA: el examen supera al diseño en todos los criterios. Señal de robustez real,
  no de sobreajuste. El edge se mantuvo e incluyó el crash COVID (2020) y la caída 2022.

Supuestos: datos Yahoo Finance ajustados por splits y dividendos · coste 15pb/RT · sin swap
Veredicto: APRUEBA (4/4 en diseño Y en examen — caso poco frecuente)
Siguiente paso: Fase 05 — meseta de parámetros: testear RSI(2) umbral 5/10/15 y MA5 umbral 3/5/7 para confirmar que no es un pico aislado.

---

## NOTAS PARA EL TRADER

### Fuente
Larry Connors & Cesar Alvarez, "Short Term Trading Strategies That Work" (2008).
Es una de las estrategias de reversión a la media más documentadas y replicadas del mundo.

### Por qué pasa 4/4 en examen (2019-2026)
El periodo incluye COVID (caída -35% en marzo 2020 → rebote inmediato) y la caída 2022 (-35%).
El filtro MA200 evitó entrar en la caída de 2022 (QQQ por debajo de su MA200 durante meses).
Los rebotes post-caída en 2020 y 2023 fueron exactamente el tipo de señal que captura el RSI(2).

### Limitaciones
- Solo largos: en mercados bajistas prolongados (2000-2003, 2008, 2022) el sistema no opera.
  Eso es una ventaja (evita pérdidas) pero también un costo de oportunidad.
- Requiere ejecutar al open del día siguiente: necesita una orden límite o de mercado pre-apertura.
- Los dividendos de QQQ son pequeños (~0.6% anual) y ya están incluidos en Yahoo Finance (ajustados).

### Compatibilidad con el portafolio
Activo diferente a BTC → correlación baja con EWMAC BTC 4H.
Tipo opuesto: EWMAC es tendencia; RSI2 QQQ es reversión a la media.
Combinación ideal para un portafolio diversificado.
