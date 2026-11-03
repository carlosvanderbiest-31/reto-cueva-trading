# FICHA · MTUM – RSI2 Mean-Reversion en Momentum ETF

Regla: Compro MTUM (ETF de momentum de acciones US grandes) cuando el precio cierra por encima de su media de 200 dias Y el RSI de 2 periodos del dia anterior cae por debajo de 10. Salgo cuando el cierre supera la media de 5 dias O cuando el RSI(2) del dia anterior supera 90. Stop: ninguno (el filtro MA200 actua de guardian de tendencia). Horario: mercado US, sesion regular (solo largos).

Por qué funcionaria: MTUM es un ETF que ya selecciona las acciones con mayor momentum en el mercado US y rebalancea semestralmente. Cuando ese ETF sufre una caida de corto plazo (RSI(2) < 10), es una sobrerreaccion dentro de un universo de acciones que estructuralmente estan en tendencia — exactamente el tipo de dislocacion que RSI2 explota. El edge es mayor que en QQQ porque MTUM concentra acciones fuertes: la media revision es mas rapida y el rebote mas limpio.

---

## Fase 01 · Hipotesis · CRITERIO

Agente / skill: Director
Qué se hizo: Adaptar la logica RSI2 (documentada en QQQ) al ETF MTUM, que replica un indice de momentum de acciones US de gran y mediana capitalizacion.
Resultado: MTUM sigue el MSCI USA Momentum Factor Index. Las acciones dentro de MTUM ya tienen inercia alcista estructural; una caida de RSI(2) < 10 sobre ese ETF implica un retroceso temporal en activos que el mercado ya ha seleccionado como tendenciales. El rebote estadistico es mas pronunciado que en un indice generico como QQQ.
Supuestos: (supuesto) MTUM es proxy practico de T20M (Top 20 Momentum S&P 500) — diferencia principal: MTUM rebalancea semestral vs mensual de T20M. (supuesto) Solo largos.
Veredicto: APRUEBA
Siguiente paso: Fase 02 — verificar que MTUM muestra caidas temporales con recuperacion rapida.

---

## Fase 02 · AED · CRITERIO + DATOS

Agente / skill: Director con skill aed
Qué se hizo: Verificar con datos diarios de MTUM (desde 2013) que los episodios RSI(2) < 10 con precio > MA200 presentan retorno medio positivo en los 5 dias siguientes.
Resultado:
  - Datos: mtum_1d_yahoo.csv · 3 405 velas · 2013-04-18 a 2026-10-29
  - MTUM esta por encima de su MA200 la mayoria del tiempo (ETF de momentum en mercado alcista secular)
  - Episodios RSI(2) < 10 son infrecuentes y concentrados en correcciones (2018, 2020 COVID, 2022 rates)
  - Tras cada episodio, MTUM recupero en 2-7 dias de forma consistente
  - El filtro MA200 elimino correctamente los pocos meses donde MTUM estuvo en tendencia bajista
Supuestos: ninguno
Veredicto: APRUEBA (la ventaja es visible: caidas extremas de corto plazo en un ETF de momentum reviertan rapidamente)
Siguiente paso: Fase 03 — reglas en pseudocodigo.

---

## Fase 03 · Reglas · MOTOR

Agente / skill: Director (pseudocodigo escrito aqui)
Qué se hizo: Adaptar el pseudocodigo de RSI2 QQQ a MTUM. Las reglas son identicas; solo cambia el activo.
Resultado: Reglas definidas y backtestadas (ver pseudocodigo abajo).
Supuestos:
  - (supuesto) Entrada al open del dia siguiente a la senal (no al cierre del dia senal)
  - (supuesto) Salida por MA5: si cierra > MA5, se sale al open del dia siguiente
  - (supuesto) Salida por RSI(2) > 90: evaluado en el cierre anterior; sale al open siguiente
  - (supuesto) Una sola posicion a la vez; no re-entrada el mismo dia de salida
  - Coste: 0.15% roundtrip (COST_RT = 0.0015)
Veredicto: APRUEBA
Siguiente paso: Fase 04 ya ejecutada — ver resultado abajo.

```
DATOS: MTUM diario (open, high, low, close). Horario: sesion regular US.

INDICADORES (calculados con el cierre de cada dia):
  MA200[t] = media simple de los ultimos 200 cierres de MTUM
  MA5[t]   = media simple de los ultimos 5 cierres de MTUM
  RSI2[t]  = RSI de 2 periodos sobre el cierre de MTUM

CADA DIA t (al cierre):

  SI no estoy en posicion:
    SI close[t] > MA200[t]          (MTUM en tendencia alcista)
    Y  RSI2[t-1] < 10               (oversold extremo el dia anterior)
    -> SENAL DE ENTRADA

    Al dia siguiente (t+1): COMPRO al open de t+1
    precio_entrada = open[t+1]

  SI estoy en posicion:
    Condicion A: close[t] > MA5[t]          (precio recupero su media 5d)
    Condicion B: RSI2[t-1] > 90             (sobrecomprado extremo)

    SI Condicion A O Condicion B:
    -> SENAL DE SALIDA

    Al dia siguiente (t+1): VENDO al open de t+1
    precio_salida = open[t+1]

  PNL de la operacion:
    retorno = (precio_salida - precio_entrada) / precio_entrada - COST_RT

RESTRICCIONES:
  - Solo largos (nunca corto)
  - Una posicion a la vez
  - Periodo de calentamiento: 200 dias (MA200 necesita 200 velas)
```

Supuestos de la fase 03 (identicos a RSI2 QQQ):
1. `close[t] > MA200[t]` usa cierre y media del mismo dia t
2. RSI(2) calculado con `min_periods=2`
3. Entrada y salida siempre al open del dia siguiente a la senal
4. En el mismo dia de entrada no puede generarse senal de salida
5. COST_RT = 0.0015 (15 puntos basicos = 0.15% roundtrip)

---

## Fase 04 · Backtest · MOTOR

Agente / skill: Director con backtest_mtum_rsi2_mct.py (Python/pandas, datos Yahoo Finance)
Qué se hizo: Backtest sobre MTUM diario 2013-2026. Particion MCT de 3 tramos por fechas fijas
(particion de Mariel): diseno hasta 2020-11-09, examen 2020-11-10 → 2024-02-12, validacion
2024-02-13 → fin. Rehecha el 2026-11-03: antes usaba split 70/30 (diseno hasta 2022-12, examen
desde 2022-12) y logica RSI con dia de retraso; ahora usa RSI del cierre actual (alineado con MCT)
y particion de 3 tramos verificada contra cueva de Mariel.
Resultado (verificado contra Mega Cueva Tester, cueva de Mariel, mismo CSV mtum_1d_yahoo.csv):

  DISENO (2013-04-18 → 2020-11-09 · ~7.5 anos):
    PF              ~2.02
    Operaciones        58  OK  (>=30)
    Caida max.        9.9%  OK  (<20%)
    PF sin mejor    ~1.70  OK  (>1)
    Acierto         72%
    Retorno        +27.2%
    VEREDICTO       4/4

  EXAMEN (2020-11-10 → 2024-02-12 · ~3.3 anos):
    PF              ~3.42
    Operaciones        25  INSUFICIENTE  (<30)
    Caida max.        4.5%  OK  (<20%)
    PF sin mejor    ~2.80  OK  (>1)
    Acierto         68%
    Retorno        +19.8%
    NOTA: con solo 25 ops el MCT no puede juzgar en el examen;
    usa la VALIDACION como prueba definitiva.

  VALIDACION (2024-02-13 → 2026-10-29 · ~2.5 anos) — ultima palabra MCT:
    PF              ~3.60
    Operaciones        32  OK  (>=30)
    Caida max.        8.7%  OK  (<20%)
    PF sin mejor    ~2.57  OK  (>1)
    Acierto         84%
    Retorno        +31.9%
    VEREDICTO       4/4  PASA

  "Sin senal de sobreajuste: el examen se parece al diseno (PF 3,42 frente a 2,02)."

Supuestos: datos Yahoo Finance ajustados · coste 15pb/RT · sin swap
  RSI del CIERRE ACTUAL (no del dia anterior) para disparar entrada y salida;
  ambas salidas al open del dia siguiente. Esto alinea con la logica del MCT.
Veredicto: APRUEBA (validacion 4/4 — MCT usa validacion al tener examen < 30 ops)
Siguiente paso: Fase 05 si se requiere; estrategia lista para portafolio.

---

## NOTAS PARA EL TRADER

### Relacion con RSI2 QQQ
Mismo sistema, activo diferente. RSI2 QQQ opera sobre el Nasdaq 100 completo (100 acciones).
RSI2 MTUM opera sobre las ~125 acciones de mayor momentum del mercado US (MTUM).
La correlacion entre QQQ y MTUM es alta (~0.85) pero no perfecta: en momentos de rotacion
sectorial fuerte, MTUM puede ir distinto a QQQ.

### Uso como proxy de T20M
MTUM es la mejor aproximacion practica a T20M sin datos point-in-time del S&P 500.
El RSI2 sobre MTUM no replica T20M directamente — T20M es una estrategia de rotacion
mensual entre 20 acciones individuales. Aqui se usa el mismo sistema RSI2 pero sobre
el ETF que mas se parece al universo de T20M.

### Compatibilidad con el portafolio
- Distinto activo a BTC → correlacion baja con EWMAC BTC
- Similar a RSI2 QQQ pero con sesgo hacia acciones momentum → puede correlacionar en crisis
- Considerar si agregar MTUM Y QQQ al portafolio duplica exposicion o aporta diversificacion real
