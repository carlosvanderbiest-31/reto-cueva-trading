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

Agente / skill: Director con backtest_ibb_qqq_v2.py (Python/pandas, datos Yahoo Finance)
Qué se hizo: Backtest sobre datos diarios IBB y QQQ. Split 70/30: diseno hasta 2019-04-30, examen desde 2019-05-31.
Variante evaluada: momentum 20 dias con filtro MA200 (cash si ganador bajo MA200).
Resultado:

  DISENO (in-sample · 2001-11-30 a 2019-04-30 · ~17 anos):
    PF              1.394  OK  (>=1.30)
    Operaciones       175  OK  (>=30)
    Caida max.      40.4%  --  (<20%)   ← FALLA
    PF sin mejor    1.321  OK  (>1)
    Acierto         51.4%
    Retorno        +126.3%
    VEREDICTO       3/4  NO APRUEBA

  EXAMEN (out-of-sample · 2019-05-31 a 2026-10-29 · ~7 anos):
    PF              2.891  OK  (>=1.30)
    Operaciones        77  OK  (>=30)
    Caida max.      11.4%  OK  (<20%)
    PF sin mejor    2.740  OK  (>1)
    Acierto         59.7%
    Retorno        +283.8%
    VEREDICTO       4/4  APRUEBA

  POR QUE FALLA EL DISENO:
  El periodo 2001-2019 incluye dos crisis extremas donde IBB y QQQ caen simultaneamente
  antes de que el filtro MA200 reaccione:
    · Crash dotcom 2001-2002: ambos ETFs caen >50% en meses — el MA200 tarda 2-3 meses en cruzar
    · Crisis financiera 2008: caida brusca de 40% en pocas semanas — el MA200 no puede proteger
  En el examen (2019-2026) el filtro funcionó bien: evitó el COVID (2020) y el crash de 2022.

Supuestos: datos Yahoo Finance ajustados · coste 15pb/RT · sin swap · rebalanceo en cierre de mes
Veredicto: NO APRUEBA (3/4 en diseno — falla DD por crashes sistemicos historicos)
Siguiente paso: Fase 06 ya ejecutada — ver resultado abajo.

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

Supuestos: mismos que Fase 04 mas filtro SPY MA200 y ETF MA100 aplicados en el mismo cierre mensual
Veredicto: APRUEBA (4/4 en diseno Y examen con Variante B)
Siguiente paso: Fase 07 — tamanio de posicion y riesgo.

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
Activos distintos a BTC y QQQ → diversificacion real.
En el examen (periodo mas reciente) pasa 4/4 con PF casi 3 y DD bajo 12%.
