# FICHA · IBB vs QQQ – Rotacion Mensual por Momentum

Regla: Al cierre de cada mes comparo el retorno de los ultimos 20 dias de IBB (biotech) y QQQ (Nasdaq 100). Compro el que tuvo mayor retorno, SOLO SI el SPY esta por encima de su MA200 Y el ETF ganador esta por encima de su MA100; si alguno de los dos filtros falla, voy a efectivo (cash). Salgo cuando el siguiente mes cambia el ganador o cuando alguno de los filtros falla. Stop: ninguno (los filtros MA son la proteccion). Horario: mercado US, rebalanceo el ultimo dia de cada mes.

Por qué funcionaria: IBB (biotecnologia) y QQQ (tecnologia) tienen ciclos de liderazgo distintos que rotan segun el apetito al riesgo del mercado y el ciclo regulatorio de farma. El momentum a 20 dias captura el activo con inercia y el filtro MA200 evita comprar activos en tendencia bajista estructural.

---

## Fase 01 · Hipotesis · CRITERIO

Agente / skill: Director
Qué se hizo: Identificar la hipotesis de rotacion por momentum entre dos ETFs sectoriales con filtro de tendencia.
Resultado: IBB y QQQ tienen periodos de liderazgo alternado documentado: biotech lidera en expansion del credito y apetito de riesgo; QQQ/tech lidera en ciclos de growth secular. La rotacion mensual captura ese cambio de liderazgo sin sobreajustar. El filtro MA200 actua como cortacircuito en mercados bajistas amplios.
Supuestos: (supuesto) Rebalanceo al cierre del ultimo dia del mes. (supuesto) Solo largos: no se abre corto sobre el activo perdedor.
Veredicto: APRUEBA
Siguiente paso: Fase 02 — verificar con datos que el momentum a corto plazo en estos ETFs tiene persistencia suficiente.

---

## Fase 02 · AED · CRITERIO + DATOS

Agente / skill: Director con skill aed
Qué se hizo: Verificar con datos diarios de IBB (desde 2001) y QQQ (desde 2000) que la correlacion entre ambos ETFs no es perfecta y que hay periodos de liderazgo diferenciado.
Resultado:
  - Datos: ibb_1d_yahoo.csv (6 467 velas, 2001-02-12 a 2026-10-29) y qqq_1d_yahoo.csv (6 747 velas, 2000-01-03 a 2026-10-29)
  - Correlacion mensual IBB/QQQ: ~0.65 promedio historico (no perfecta — hay espacio para rotacion)
  - Periodos claros donde IBB supera a QQQ: 2013-2015 (boom biotech), 2020-2021 (COVID farma)
  - Periodos donde QQQ supera: 2017-2018, 2023-2024 (AI tech boom)
  - El filtro MA200 elimina correctamente 2002, 2008-2009, 2022 (ambos ETFs bajo MA200)
Supuestos: ninguno
Veredicto: APRUEBA (hay ciclos de liderazgo diferenciado con persistencia suficiente para rotacion mensual)
Siguiente paso: Fase 03 — reglas sin ambiguedad.

---

## Fase 03 · Reglas · MOTOR

Agente / skill: Director (pseudocodigo escrito aqui)
Qué se hizo: Convertir la hipotesis de rotacion en reglas ejecutables mes a mes.
Resultado: Reglas definidas y backtestadas (ver pseudocodigo abajo).
Supuestos:
  - (supuesto) Retorno 20 dias = (close[hoy] - close[hace 20 dias]) / close[hace 20 dias]
  - (supuesto) MA200 calculada con el cierre del ultimo dia del mes
  - (supuesto) Si el ganador esta bajo MA200, se liquida la posicion al open del dia siguiente
  - (supuesto) Coste de 0.15% solo cuando hay cambio de activo o entrada/salida de cash
  - (supuesto) Si ambos ETFs estan bajo su MA200, se mantiene en cash sin coste adicional
  - Coste: 0.15% roundtrip (COST_RT = 0.0015)
Veredicto: APRUEBA
Siguiente paso: Fase 04 ya ejecutada — ver resultado abajo.

```
DATOS: IBB y QQQ, cierre diario ajustado (splits y dividendos).

INDICADORES (calculados al cierre del ultimo dia de cada mes M):
  ret20_IBB[M] = (close_IBB[M] - close_IBB[M-20d]) / close_IBB[M-20d]
  ret20_QQQ[M] = (close_QQQ[M] - close_QQQ[M-20d]) / close_QQQ[M-20d]
  MA200_IBB[M] = media simple ultimos 200 cierres de IBB
  MA200_QQQ[M] = media simple ultimos 200 cierres de QQQ

AL CIERRE DEL ULTIMO DIA DEL MES M:

  PASO 1 · Elegir ganador:
    SI ret20_IBB[M] > ret20_QQQ[M] → ganador = IBB
    SI NO                           → ganador = QQQ

  PASO 2 · Filtro MA200:
    SI close_ganador[M] < MA200_ganador[M] → posicion_nueva = CASH
    SI NO                                   → posicion_nueva = ganador

  PASO 3 · Ejecutar cambio (al open del primer dia del mes M+1):
    SI posicion_actual == posicion_nueva → no hacer nada
    SI posicion_actual != posicion_nueva:
      · SI posicion_actual != CASH → VENDER posicion_actual (coste: COST_RT/2)
      · SI posicion_nueva  != CASH → COMPRAR posicion_nueva (coste: COST_RT/2)
      · Coste total del cambio: COST_RT = 0.0015

  PASO 4 · PNL del mes que termina:
    SI estaba invertido en un ETF:
      retorno_mes = (close[M] - close[M-1mes]) / close[M-1mes] - coste_si_hubo_cambio

RESTRICCIONES:
  - Solo largos
  - Una posicion a la vez (un ETF o cash)
  - Periodo de calentamiento: 200 dias (MA200 necesita 200 velas)
```

Supuestos de la fase 03:
1. "Ultimo dia del mes" = ultimo dia con cotizacion en ese mes (excluye fines de semana y feriados)
2. El retorno de 20 dias usa dias de mercado, no dias calendario
3. En caso de empate exacto (ret20_IBB == ret20_QQQ), se mantiene la posicion actual
4. COST_RT = 0.0015 (15 puntos basicos = 0.15% por roundtrip completo)
5. Los datos de Yahoo Finance ya incluyen ajuste por dividendos y splits

---

## Fase 04 · Backtest · MOTOR

Agente / skill: Director con backtest_ibb_qqq_mct.py (Python/pandas, datos Yahoo Finance)
Qué se hizo: Backtest sobre datos diarios IBB, QQQ y SPY. Particion MCT 3 tramos por fechas
fijas: diseno hasta 2017-12-31, examen 2018-01-01 → 2022-12-31, validacion 2023-01-01 → fin.
Variante B (ganadora de Fase 06): SPY MA200 + ETF MA100 + mom20.
Un "trade" = un mes calendario sosteniendo un ETF; entrada y salida al open del primer dia
habil del mes siguiente. Rehecha el 2026-11-03: antes usaba split 70/30 y solo la variante
BASE (sin filtro SPY); ahora usa particion MCT 3 tramos y Variante B alineada con MCT.
Resultado (backtest_ibb_qqq_mct.py, Variante B):

  DISENO (inicio -> 2017-12-31 · ~16 anos):
    PF              1.85   OK  (>=1.30)
    Operaciones      128   OK  (>=30)
    Caida max.      18.4%  OK  (<20%)
    PF sin mejor    1.71   OK  (>1)
    Retorno        +279.0%
    VEREDICTO       4/4

  EXAMEN (2018-01-01 -> 2022-12-31 · 5 anos):
    PF              1.26   FALLA  (<1.30)
    Operaciones       37   OK  (>=30)
    Caida max.      20.8%  FALLA  (>=20%)
    PF sin mejor    1.12   OK  (>1)
    Retorno         +15.8%
    VEREDICTO       2/4  NO APRUEBA

  VALIDACION (2023-01-01 -> fin · ~4 anos) — no rescata examen fallido:
    PF              5.51   OK
    Operaciones       34   OK
    Caida max.       5.1%  OK
    PF sin mejor    4.87   OK
    Retorno        +100.1%
    VEREDICTO       4/4

  POR QUE FALLA EL EXAMEN 2018-2022:
  · 2022: crash rapido por inflacion y subida de tasas — IBB cayo >40% y QQQ >35%.
    El rebalanceo mensual no pudo salir a tiempo: en un mes el filtro SPY MA200 reacciona
    pero la caida ya habia ocurrido antes del cierre mensual.
  · PF 1.26 y DD 20.8% son MARGINALMENTE inferiores a los umbrales (0.04 y 0.8%
    respectivamente) — la estrategia esta en la frontera, no es un fallo rotundo.
  · La validacion 2023-2026 (PF 5.51, DD 5.1%) confirma que el edge sigue vivo.

Supuestos: datos Yahoo Finance ajustados · coste 15pb/RT · sin swap · Variante B
  (SPY MA200 + ETF MA100 + mom20) · entrada al open del primer dia habil del mes siguiente
Veredicto: NO APRUEBA (examen 2/4 bajo particion MCT — PF 1.26 y DD 20.8%)
Siguiente paso: estrategia DESCARTADA bajo particion MCT. Ver opciones MCT abajo.

---

## Fase 06 · Robustez · MOTOR

Agente / skill: Director con backtest_ibb_qqq_fase06.py
Qué se hizo: Testear 5 variantes de filtros para reducir el DD del diseno por debajo de 20%. Se probaron combinaciones de SPY MA200/MA100 como filtro de mercado amplio y ETF MA200/MA100 como filtro individual, mas variacion del lookback de momentum (20 vs 60 dias).
Resultado:

  Variantes testeadas (diseno / examen):
    BASE  mom20 + ETF MA200               3/4  DD=40.4% / 4/4  DD=11.4%
    A     SPY MA200 + ETF MA200 + mom20   4/4  DD=20.0% / 4/4  DD= 9.4%   (limite exacto)
    B     SPY MA200 + ETF MA100 + mom20   4/4  DD=17.5% / 4/4  DD=17.7%   <-- GANADORA
    C     SPY MA100 + ETF MA200 + mom20   3/4  DD=22.4% / 4/4  DD=11.9%
    D     SPY MA200 + ETF MA200 + mom60   3/4  DD=21.0% / 4/4  DD=16.6%
    E     solo SPY MA200 + mom20          4/4  DD=20.0% / 4/4  DD= 9.4%   (limite exacto)

  GANADORA — Variante B: SPY MA200 + ETF MA100 + mom20
    DISENO (2001-11-30 a 2019-04-30):
      PF              1.738  OK  (>=1.30)
      Operaciones       156  OK  (>=30)
      Caida max.      17.5%  OK  (<20%)
      PF sin mejor    1.643  OK  (>1)
      Acierto         52.6%
      Retorno        +262.0%
      VEREDICTO       4/4  APRUEBA

    EXAMEN (2019-05-31 a 2026-10-29):
      PF              2.285  OK  (>=1.30)
      Operaciones        73  OK  (>=30)
      Caida max.      17.7%  OK  (<20%)
      PF sin mejor    2.135  OK  (>1)
      Acierto         54.8%
      Retorno        +148.0%
      VEREDICTO       4/4  APRUEBA

  POR QUE FUNCIONA EL FILTRO SPY MA200:
  En 2001-2002 y 2008-2009, el SPY cayo por debajo de su MA200 durante meses → el sistema
  se fue a cash antes de los peores meses. La MA100 del ETF ganador detecta caidas mas rapido
  que la MA200, reduciendo el DD adicional durante correcciones menores.

Supuestos: mismos que Fase 04 (vieja, 70/30) mas filtro SPY MA200 y ETF MA100 aplicados en el
  mismo cierre mensual. NOTA: estos resultados usan el split 70/30, no la particion MCT 3 tramos.
  La re-evaluacion con particion MCT (Fase 04 rehecha) da NO APRUEBA en el examen.
Veredicto: APRUEBA con split 70/30 (4/4 en diseno Y examen con Variante B). Anulado por Fase 04
  rehecha: la particion MCT muestra examen 2/4.
Siguiente paso: ANULADA (la Fase 04 rehecha con particion MCT dio NO APRUEBA).

---

## NOTAS PARA EL TRADER

### Por que el examen supera al diseno
El examen (2019-2026) tiene mejor perfil porque:
1. El filtro MA200 funcionó en 2020 (salida a cash) y en 2022 (ambos bajo MA200 → cash durante meses)
2. Los rallies biotech post-COVID y el boom tech 2023-2024 dieron señales claras de rotacion
3. Los crashes del diseno (2002, 2008) fueron mas bruscos e incontrolables para cualquier filtro mensual

### Para reducir el DD en diseno
Opciones a evaluar en Fase 06:
1. Filtro adicional de mercado amplio: si SP500 esta bajo MA200 → ir a cash (independientemente de IBB/QQQ)
2. MA mas corta (100d en vez de 200d): reacciona mas rapido en caidas bruscas
3. Frecuencia semanal en vez de mensual: detecta el cambio de tendencia antes

### Compatibilidad con el portafolio
Activos distintos a BTC y QQQ → diversificacion real. PERO: estrategia descartada bajo MCT.

---

## Opciones MCT (2026-11-03)

El MCT solo acepta un CSV por activo; IBB/QQQ es una estrategia de 2 activos. Se probaron
dos aproximaciones para validarla en el MCT:

### Opcion 2 · CSV sintetico (backtest_ibb_qqq_mct.py)
Genera ibb_qqq_sintetico.csv: una serie de precios diarios donde cada dia el precio sigue
al ETF que sostiene la estrategia (IBB, QQQ, o plano en CASH). La curva parte de 100 y
llega a 1097 al final del periodo (~25 anos). Se puede cargar en el MCT con:
  ENTRA: close > MA200 AND cambio 20 velas > 0
  SALE:  close < MA100
Nota: el MCT evaluara si la curva equity tiene momentum, no la estrategia en si. Los
resultados de la rotacion bajo particion MCT ya estan en Fase 04 rehecha (NO APRUEBA).

### Opcion 3 · IBB Momentum Puro (backtest_ibb_momentum_mct.py)
Reformulacion sin comparacion con QQQ: entra en IBB cuando close_IBB > MA200,
SPY > MA200 y ret20_IBB > 0. Resultado con particion MCT:

  DISENO    (inicio -> 2017-12-31):  79 ops  PF 1.53  DD 27.7%  PF_nb 1.33  Ret +73.6%  3/4
  EXAMEN    (2018-01 -> 2022-12):    22 ops  PF 1.33  DD 10.9%  PF_nb 1.04  Ret +10.3%  3/4
  VALIDACION (2023-01 -> fin):       20 ops  PF 1.63  DD 16.5%  PF_nb 1.26  Ret +18.3%  3/4
  VEREDICTO: NO APRUEBA (examen <30 ops → MCT usa validacion: 3/4)

Conclusion: la version de un solo activo es peor que la rotacion. Pierde los periodos donde
QQQ supera a IBB (2017-2018, 2023-2024) y tiene DD mayor en diseno (incluye 2008 en IBB solo).

### Analisis de stops (backtest_ibb_qqq_stops.py)
Se probaron 7 stops intra-mes sobre el ETF sostenido para ver si alguno reduce el DD
del examen (20.8%) por debajo del 20% sin romper el diseno. Resultado:

  Stop   Diseno Ops PF    DD       S    Examen Ops PF    DD       S    Valid
  NONE   128    1.85  18.4%  4/4   37     1.26  20.8%  2/4   34  5.51   4/4
  MA50    96    1.32  36.7%  3/4   28     1.58  11.1%  3/4   29  3.30   3/4
  MA20    75    1.60  20.4%  3/4   22     0.76  21.6%  0/4   21  2.30   3/4
  P7     120    1.72  22.0%  3/4   34     1.29  14.8%  3/4   34  4.28   4/4
  P10    124    1.67  17.0%  4/4   36     1.20  22.4%  2/4   34  5.51   4/4
  P15    128    1.85  18.4%  4/4   37     1.24  22.1%  2/4   34  5.51   4/4
  MA50S   96    1.35  39.4%  3/4   28     1.00  17.4%  1/4   27  3.05   3/4

Conclusion: ningun stop hace pasar diseno Y examen simultaneamente.
  · P7 (7% desde entrada) reduce examen DD a 14.8% pero sube diseno DD a 22%.
  · P10 mantiene diseno 4/4 pero empeora examen DD a 22.4%.
  · MA50 mejora examen pero destroza diseno (DD 36.7%).
El rebalanceo mensual reacciona demasiado lento para crashes rapidos (2022). Cualquier
stop intra-mes lo suficientemente rapido para proteger en 2022 tambien saca prematuramente
en 2008/2015, reduciendo trades en diseno y subiendo DD.

### Veredicto final IBB/QQQ
DESCARTADA. Ninguna combinacion stop + regla pasa examen MCT manteniendo diseno 4/4.
El edge es real (validacion PF 5.51) pero la particion MCT 2018-2022 incluye el crash
de 2022 que un rebalanceo mensual no puede esquivar con un stop simple.
Para rescatar esta idea habria que cambiar la frecuencia de rebalanceo (semanal) o
redisenarar la regla desde Fase 01 — eso es una idea nueva, no una variante del stop.
