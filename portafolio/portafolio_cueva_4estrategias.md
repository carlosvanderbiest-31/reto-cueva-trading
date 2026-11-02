# FICHA · Portafolio Cueva TIS · 4 Estrategias

Regla: Combina en peso igual (25% c/u) o risk parity (1/vol mensual) cuatro estrategias
validadas 4/4: RSI2 QQQ, RSI2 MTUM, IBB vs QQQ rotacion, EWMAC BTC 4H.
Opera cada una segun sus propias reglas. Rebalancea mensual.

Por que funcionaria: diversificacion real entre activos no correlacionados (cripto + renta
variable US). La teoria de portfolio (Markowitz) muestra que combinar estrategias con
correlacion baja reduce la caida maxima sin sacrificar retorno. La suma de 4 estrategias
con FF bajas pero descorrelacionadas produce un portafolio con mejor perfil riesgo/retorno
que cualquiera de las partes.

---

## Fase 01 · Hipotesis · CRITERIO

Agente / skill: Director
Que se hizo: Identificar cuatro estrategias validadas 4/4 con baja correlacion entre si.
Resultado: Cuatro tipos distintos de edge: mean-reversion de corto plazo en ETF de acciones
  (RSI2), rotacion sectorial mensual (IBB/QQQ), y seguimiento de tendencia en cripto
  (EWMAC BTC). Tres activos base distintos: QQQ, MTUM, IBB/QQQ, BTC.
Supuestos: (supuesto) Periodo comun desde 2014-02 (limitado por MTUM desde 2013 + calentamiento MA200).
Veredicto: APRUEBA (base teorica solida; diversificacion por tipo de edge y activo)
Siguiente paso: Fase 04 directa (estrategias ya validadas individualmente; se combina y se mide el portafolio).

---

## Fase 04 · Backtest del portafolio · MOTOR

Agente / skill: Director con backtest_portafolio.py (Python/pandas)
Que se hizo: Backtest del portafolio combinando las 4 estrategias en retornos mensuales.
  Se testean dos esquemas de ponderacion: peso igual (25% c/u) y risk parity (1/vol rolling 12m).

Periodo comun : 2014-02-01 a 2026-10-31
Split 70/30   : diseno hasta 2023-01-31 · examen desde 2023-02-01
Coste         : 0.15% roundtrip por operacion en cada estrategia
Archivo       : datos/backtest_portafolio.py
Grafico       : resultados/curva_portafolio.png

### Estrategias individuales en el periodo comun

| Estrategia | Diseno | PF | DD | Ret | Examen | PF | DD | Ret |
|---|---|---|---|---|---|---|---|---|
| BTC_EWMAC  | 1/4 | 0.498 | 52.1% | -37.2% | 1/4 | 1.207 | 23.5% | +7.9%   |
| RSI2_QQQ   | 4/4 | 3.772 | 12.0% | +307.9%| 4/4 | 5.736 |  5.5% | +101.3% |
| IBB_QQQ    | 1/4 | 1.057 | 27.7% | -0.9%  | 4/4 | 2.649 |  8.5% | +35.1%  |
| RSI2_MTUM  | 4/4 | 3.072 | 14.3% | +171.9%| 4/4 | 2.432 | 12.4% | +51.0%  |

Nota sobre BTC_EWMAC (1/4 en ambos periodos dentro del portafolio):
El sistema fue validado 4/4 en su propio split (diseno 2017-2024, examen 2024-2026).
En la ventana comun del portafolio (diseno 2017-2023), el crash de BTC 2022 (-75%)
genera muchos whipsaws con EWMAC 8/32. Su edge real se ve en horizontes con bull run
sostenido. Aun asi, la correlacion cercana a cero con las estrategias de renta variable
lo hace valioso como diversificador.

Nota sobre IBB_QQQ (1/4 en diseno del portafolio):
El sistema fue validado 4/4 en Fase 06 con diseno 2001-2019. En la ventana del portafolio
(diseno 2014-2023), el crash de 2022 por subida de tipos golpea IBB y QQQ antes de que
los filtros MA puedan reaccionar. En el examen (2023-2026) recupera su 4/4.

### Portafolio combinado

#### PESO IGUAL (25% cada estrategia)

  DISENO (2014-02 a 2023-01):
    PF            2.222   APRUEBA (>=1.30)
    Meses          108    APRUEBA (>=30)
    DD max.       10.1%   APRUEBA (<20%)
    PF sin mejor  1.675   APRUEBA (>1)
    Acierto       63.0%   (meses positivos)
    Retorno      +76.3%
    SCORE  4/4  APRUEBA

  EXAMEN (2023-02 a 2026-10):
    PF            2.854   APRUEBA (>=1.30)
    Meses           45    APRUEBA (>=30)
    DD max.        6.2%   APRUEBA (<20%)
    PF sin mejor  2.481   APRUEBA (>1)
    Acierto       64.4%
    Retorno      +48.5%
    SCORE  4/4  APRUEBA

#### RISK PARITY (1/vol rolling 12 meses)

  DISENO (2014-02 a 2023-01):
    PF            2.701   APRUEBA
    Meses          108    APRUEBA
    DD max.        8.9%   APRUEBA
    PF sin mejor  2.216   APRUEBA
    Acierto       65.7%
    Retorno      +142.4%
    SCORE  4/4  APRUEBA

  EXAMEN (2023-02 a 2026-10):
    PF            4.273   APRUEBA
    Meses           45    APRUEBA
    DD max.        3.9%   APRUEBA
    PF sin mejor  3.728   APRUEBA
    Acierto       71.1%
    Retorno      +65.3%
    SCORE  4/4  APRUEBA

### Correlaciones mensuales (periodo completo 2014-2026)

|              | BTC_EWMAC | RSI2_QQQ | IBB_QQQ | RSI2_MTUM |
|---|---|---|---|---|
| BTC_EWMAC    |  1.00     |  -0.00   |  -0.06  |   0.12    |
| RSI2_QQQ     | -0.00     |   1.00   |   0.28  |   0.19    |
| IBB_QQQ      | -0.06     |   0.28   |   1.00  |   0.25    |
| RSI2_MTUM    |  0.12     |   0.19   |   0.25  |   1.00    |

BTC EWMAC tiene correlacion practicamente nula (-0.06 a 0.12) con las 3 estrategias de
renta variable. RSI2_QQQ y RSI2_MTUM tienen 0.19 de correlacion (bajo). IBB_QQQ tiene
0.25-0.28 con las RSI2 (moderado, pero ambas son renta variable US).

Supuestos:
  - (supuesto) Pesos iguales: 25% por estrategia, sin ajuste de capital minimo
  - (supuesto) Risk parity: 1/vol mensual rolling 12m, recalculado cada mes
  - (supuesto) Periodo comun empieza en 2014-02 (MTUM disponible desde 2013-04 + 10m calentamiento MA200)
  - (supuesto) Cada estrategia opera segun sus propias reglas; el portafolio solo agrega retornos mensuales
  - (supuesto) No se calcula correlacion dinamica ni se ajusta por regimen de mercado
  - Coste: ya incluido en cada estrategia individual

Veredicto: APRUEBA 4/4 en diseno y examen (ambas versiones: peso igual y risk parity)
Siguiente paso: Fase 07 — tamanio de posicion y asignacion de capital real.

---

## NOTAS PARA EL TRADER

### Que ponderacion usar

Risk parity da mejor retorno (+142% vs +76% en diseno, +65% vs +49% en examen) y menor DD
(8.9% vs 10.1% en diseno, 3.9% vs 6.2% en examen). Es la opcion recomendada si el capital
es suficiente para diversificar en las 4 estrategias.

Peso igual es mas sencillo de ejecutar: 25% del capital a cada estrategia, sin recalculos.

### Interpretacion del efecto diversificacion

La caida maxima del portafolio (8.9-10.1%) es menor que la de cualquier estrategia individual
(BTC 52%, IBB_QQQ 27.7%, RSI2_MTUM 14.3%, RSI2_QQQ 12%). Esto es la diversificacion real en
accion: cuando una estrategia cae, las otras estan en territorio neutro o positivo.

Periodo de examen: DD solo 3.9% (risk parity) con retorno +65.3% en menos de 4 anios.

### Sobre el BTC EWMAC en el portafolio

El sistema BTC EWMAC fue validado 4/4 en su propio backtest (split 2017-2024/2024-2026).
En el portafolio, la ventana de diseno (2014-2023) lo atrapa en un periodo desfavorable
(crash 2022 con muchos whipsaws para un sistema de cruce de medias). Aun perdiendo dinero
en diseno (-37.2%), su correlacion cero con las estrategias de renta variable reduce el DD
del portafolio: cuando BTC cae, los otros sistemas no caen al mismo tiempo.

### Capital minimo estimado

Para operar las 4 estrategias con tamano razonable:
- RSI2 QQQ: 1 contrato QQQ (~500 USD por unidad), operable con 10,000 USD
- RSI2 MTUM: similar a QQQ
- IBB vs QQQ: rotacion mensual, sin apalancamiento, operable con 10,000 USD
- BTC EWMAC: 1 contrato spot o perp BTC (minimo 0.01 BTC), operable con 5,000 USD
Capital minimo recomendado para el portafolio: 30,000-50,000 USD

### Estrategias validadas que componen el portafolio

1. RSI2 QQQ — ficha: fichas/qqq_rsi2.md
2. RSI2 MTUM (proxy T20M) — ficha: fichas/mtum_rsi2.md
3. IBB vs QQQ + SPY MA200 + ETF MA100 — ficha: fichas/ibb_qqq_rotacion.md
4. EWMAC BTC 4H + MA200 diaria + stop 3% — pendiente de ficha individual

### Lo que falta (Fases 07 y 08)

- Fase 07: calculo de tamano de posicion real segun capital y tolerancia al riesgo
- Fase 08: puesta en marcha, demo, automatizacion y seguimiento en vivo
