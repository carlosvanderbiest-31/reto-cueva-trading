# FICHA · S&P 500 – T20M Top 20 Momentum

Regla: Cada mes ranqueo los 500 stocks del S&P 500 por momentum de 12 meses (ajustado por volatilidad de 6 meses). Compro los 20 mejores en peso igual. Rebalancea mensual: vendo los que salen del top 20, compro los nuevos. Stop: ninguno (la salida es la exclusion del top 20 en el siguiente rebalanceo). Horario: mercado US, rebalanceo el ultimo dia de cada mes.

Por qué funcionaria: el momentum entre acciones es una de las anomalias mas estudiadas y documentadas en finanzas. Las acciones que mas subieron en los ultimos 12 meses tienden a seguir subiendo los proximos 1-6 meses. Seleccionar los top 20 concentra el portfolio en los ganadores con mayor inercia. El ajuste por volatilidad (dividir el retorno por la desviacion estandar) favorece acciones con momentum limpio vs momentum volatil.

Fuente: estrategia propia de Trade It Simple (TIS), inspirada en la literatura de momentum de Gary Antonacci y Meb Faber.

---

## Fase 01 · Hipotesis · CRITERIO

Agente / skill: Director
Qué se hizo: Identificar la hipotesis de momentum cross-sectional en acciones del S&P 500.
Resultado: El efecto momentum en acciones individuales esta documentado desde Jegadeesh & Titman (1993). Las acciones con mayor retorno en los ultimos 12 meses (excluyendo el ultimo mes para evitar el reversal de corto plazo) superan sistematicamente a las de menor retorno. Concentrar en top 20 maximiza el efecto a costa de mayor concentracion y tracking error.
Supuestos: (supuesto) El universo es el S&P 500 actual como proxy (con sesgo de supervivencia). (supuesto) Pesos iguales entre los 20 seleccionados.
Veredicto: APRUEBA (base academica solida; el efecto momentum es real y persistente)
Siguiente paso: Fase 02 — para ejecutarla correctamente se necesitan datos "point-in-time" del S&P 500 (ver nota abajo).

---

## Fase 02 · AED · CRITERIO + DATOS

Agente / skill: Director
Qué se hizo: Evaluar disponibilidad de datos para el universo S&P 500 historico.
Resultado:
  - PROBLEMA CRITICO: para evitar el sesgo de supervivencia, se necesitan los miembros del S&P 500
    tal como estaban en cada momento historico ("point-in-time"), no los 500 actuales.
  - Si usamos los 500 actuales, el backtest sobreestima el resultado porque incluye acciones que
    "sobrevivieron" hasta hoy y excluye las que quebraron o fueron expulsadas del indice.
  - Datos point-in-time del S&P 500 no estan disponibles gratuitamente en Yahoo Finance ni yfinance.
  - Fuentes pagas: Compustat, Bloomberg, Sharadar (Quandl/Nasdaq Data Link), Portfolio123.
  - Alternativa practica: usar MTUM (iShares MSCI USA Momentum Factor ETF, desde 2013) como proxy.
    MTUM implementa momentum ajustado por riesgo en acciones US grandes — el concepto mas cercano a T20M.
Supuestos: ninguno
Veredicto: PENDIENTE (faltan datos point-in-time del S&P 500 para un backtest libre de sesgo)
Siguiente paso: Bajar datos de MTUM como proxy y ejecutar Fase 04 con ese ETF, marcando el sesgo.

---

## Fase 03 · Reglas · MOTOR

Agente / skill: Director (pseudocodigo escrito aqui)
Qué se hizo: Escribir las reglas de T20M en pseudocodigo completo.
Resultado: Reglas definidas (ver pseudocodigo abajo). Pendiente de validacion con datos correctos.
Supuestos:
  - (supuesto) Universo: S&P 500 point-in-time al inicio de cada mes (no el actual)
  - (supuesto) Momentum = retorno de los ultimos 12 meses excluyendo el mes mas reciente (meses -12 a -1)
  - (supuesto) Ajuste por volatilidad = retorno_12m / desviacion_estandar_6m_retornos_diarios
  - (supuesto) Seleccion: top 20 por momentum ajustado por volatilidad
  - (supuesto) Pesos iguales (5% por accion)
  - (supuesto) Rebalanceo al cierre del ultimo dia del mes
  - Coste: 0.15% por operacion de compra o venta individual
Veredicto: APRUEBA (reglas sin ambiguedad)
Siguiente paso: Fase 04 con datos correctos (point-in-time) o con MTUM como proxy.

```
DATOS: historial de precios diarios de los miembros del S&P 500 (point-in-time por mes).

INDICADORES (calculados al cierre del ultimo dia del mes M para cada accion i):
  ret12m[i,M]  = retorno acumulado desde M-12meses hasta M-1mes (excluye el mes actual)
  vol6m[i,M]   = desviacion estandar de los retornos diarios de los ultimos 6 meses
  score[i,M]   = ret12m[i,M] / vol6m[i,M]   (momentum ajustado por riesgo)

AL CIERRE DEL ULTIMO DIA DEL MES M:

  PASO 1 · Rankear:
    Ordenar todas las acciones del S&P 500 por score[i,M] de mayor a menor
    top20[M] = las 20 primeras de ese ranking

  PASO 2 · Rebalancear:
    Para cada accion en el portfolio actual que NO este en top20[M]:
      VENDER al open del primer dia de M+1

    Para cada accion en top20[M] que NO este en el portfolio actual:
      COMPRAR al open del primer dia de M+1

    Peso objetivo de cada accion en top20[M]: 5% del capital total (peso igual)

  PASO 3 · PNL:
    retorno_mes[i] = (close[i,M] - close[i,M-1mes]) / close[i,M-1mes] - coste_si_hubo_cambio
    retorno_portfolio[M] = promedio_ponderado(retorno_mes de las 20 acciones)

RESTRICCIONES:
  - Solo largos
  - 20 posiciones a la vez en peso igual (5% cada una)
  - Se opera a nivel de accion individual (no ETF)
  - Periodo de calentamiento: 12 meses (para calcular ret12m)
```

Supuestos de la fase 03:
1. "Point-in-time" significa usar solo acciones que eran miembros del S&P 500 en ese mes
2. Las acciones que fueron adquiridas, quebraron o salieron del indice se tratan como venta forzosa
3. COST_RT = 0.0015 por cada operacion de compra o venta individual
4. Si hay menos de 20 acciones con datos suficientes, se opera con las disponibles
5. Los datos deben estar ajustados por splits y dividendos

---

## Fase 04 · Backtest · MOTOR

Agente / skill: Director con backtest_t20m.py (Python/pandas, 460 acciones S&P 500 via Yahoo Finance)
Qué se hizo: Backtest con 460 acciones del S&P 500 actual (sesgo de supervivencia declarado).
Universo: 460 acciones con datos desde 2005. Split 70/30: diseno hasta 2020-03-31, examen desde 2020-04-30.
Tres variantes testeadas segun filtro de mercado amplio (SPY):

  VARIANTE 1 — Sin filtro SPY:
    DISENO (2005-2020):  PF=1.681  Meses=170  DD=51.8%  PFnb=1.626  → 3/4  (falla DD)
    EXAMEN (2020-2026):  PF=2.260  Meses= 78  DD=19.7%  PFnb=2.064  → 4/4  APRUEBA

  VARIANTE 2 — Con filtro SPY MA200 (ir a cash si SPY < MA200):
    DISENO (2005-2020):  PF=2.502  Meses=142  DD=22.4%  PFnb=2.412  → 3/4  (falla DD por 2.4%)
    EXAMEN (2020-2026):  PF=2.014  Meses= 71  DD=19.9%  PFnb=1.868  → 4/4  APRUEBA

  VARIANTE 3 — Con filtro SPY MA100 (reacciona mas rapido):
    DISENO (2005-2020):  PF=2.334  Meses=143  DD=14.4%  PFnb=2.241  → 4/4  APRUEBA
    EXAMEN (2020-2026):  PF=1.874  Meses= 71  DD=24.7%  PFnb=1.727  → 3/4  (falla DD)

  DIAGNOSTICO: hay un tradeoff estructural entre los dos periodos.
    - El MA200 protege bien en el examen (2022 rate crash) pero no es suficiente para 2008.
    - El MA100 evita el crash de 2008 (sale antes) pero en 2020-2026 sale a cash durante
      correcciones que se recuperan rapido y pierde parte del rebote → DD de 24.7%.
    - Ninguna variante con este universo y metodologia pasa 4/4 en ambos periodos a la vez.

  EFECTO SESGO DE SUPERVIVENCIA: los resultados estan inflados porque el universo excluye
    empresas que quebraron o fueron expulsadas del S&P 500 entre 2005 y 2026.
    Los resultados reales de T20M son probablemente menores en PF y mayores en DD.

Supuestos: datos Yahoo Finance ajustados · universo S&P 500 actual (sesgo supervivencia) ·
           coste 0.075% por accion comprada o vendida · ranking mensual al ultimo dia del mes
Veredicto: NO APRUEBA (ninguna variante pasa 4/4 en ambos periodos con nuestros datos)
Siguiente paso: Para aprobar se necesitan datos point-in-time del S&P 500 (Compustat/Sharadar)
               o un mecanismo adicional de control de DD intra-mes que Mariel posiblemente usa.

---

## NOTAS PARA EL TRADER

### Por que es compleja esta estrategia
A diferencia de RSI2 QQQ (1 ETF, 1 regla simple), T20M requiere:
1. Datos de 500 acciones individuales con historial limpio
2. Datos point-in-time del indice (quien era miembro en cada fecha)
3. Capacidad de ejecutar 20-40 ordenes al mes (cambios en el top 20)
4. Mas capital para diversificar en 20 posiciones sin que los costes erosionen el retorno

### Alternativa practica inmediata
Bajar MTUM desde Yahoo Finance y testear como si fuera un ETF mas.
Ticker: MTUM, disponible desde 2013-04-17.
Limitacion: MTUM rebalancea semestral, no mensual. El backtest subestimaraa el edge real de T20M.

### Comparacion con lo que ya tenemos
T20M es momentum en acciones individuales → baja correlacion con RSI2 QQQ (mean-reversion) y con EWMAC BTC (cripto). Es el tercer tipo de estrategia distinto en el portafolio.
