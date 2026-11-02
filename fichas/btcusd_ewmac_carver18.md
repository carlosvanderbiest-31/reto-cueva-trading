# FICHA · BTC/USD – EWMAC Cesta Carver (Estrategia 18)

Regla: Compro BTC cuando la EWM(32d) cruza arriba la EWM(128d) sobre el índice de la cesta crypto.
Vendo y abro corto cuando la EWM(32d) cruza abajo la EWM(128d). Salgo cuando el cruce se invierte.
Stop: ninguno (el propio cruce de EWMs es la salida). Horario: 24/7 (cripto).

Por qué funcionaría: BTC muestra tendencias prolongadas de semanas a meses.
Un sistema que identifica la dirección del trend con dos EMAs lentas (32 días y 128 días)
puede capturar las grandes oscilaciones — como la caída de 2022 o el rally de 2024 —
con muchas menos operaciones que un sistema de reversión.
Esta es la lógica central de Robert Carver en "Advanced Futures Trading Strategies"
(Estrategia 18: trend following por clase de activo / cesta).

---

## Fase 01 · Hipótesis · CRITERIO

Agente / skill: Director (sin agente, hipótesis de libro)
Qué se hizo: Identificar la hipótesis de Carver Estrategia 18 y adaptarla a BTC.
Resultado: BTC tiene tendencias estructurales de semanas-meses (mercados alcistas/bajistas de 6-18 meses).
  El EWMAC(32d, 128d) captura esos ciclos con señal binaria o continua.
  La "cesta" original requiere varios activos de la misma clase (BTC + ETH + otros);
  con un solo activo la cesta colapsa a EWMAC directo sobre BTC.
Supuestos: (supuesto) Usamos BTC solo como cesta mínima de 1 activo.
  Para la cesta completa se necesitaría descargar ETH/USD u otros.
Veredicto: APRUEBA (hay base teórica sólida; el efecto momentum en crypto es conocido)
Siguiente paso: AED para confirmar que el trend es estadísticamente visible en los datos.

---

## Fase 02 · AED · CRITERIO + DATOS

Agente / skill: Director con skill aed
Qué se hizo: Verificar que BTC muestra tendencia estructural en el periodo de diseño (2021-10-27 → 2024-08-14).
Resultado:
  - Datos: btcusd_1h_alpaca.csv · APTA CON AVISOS · 24,547 velas de diseño
  - El periodo incluye: ATH nov-2021 (~$65k) → crash 2022 (~$16k) → recuperación 2023 → rally 2024 (~$60k)
  - Tendencia visible: el precio pasó meses arriba y meses abajo sin volver al centro → favorable para EWMAC lento
  - Señal EWMAC 32d/128d se mantuvo en la misma dirección durante periodos de 3-12 meses → tendencia real
  - Sin AED formal por hora (no aplica al trend-following mensual): se mide la tendencia de largo plazo
Supuestos: ninguno
Veredicto: APRUEBA (el activo muestra tendencias de suficiente duración para el EWMAC lento)
Siguiente paso: Reglas exactas y backtest.

---

## Fase 03 · Reglas · MOTOR

Agente / skill: Director (pseudocódigo escrito aquí)
Qué se hizo: Convertir la hipótesis Carver-18 en reglas sin ambigüedad para BTC/USD 1h.
Resultado: Reglas definidas y backtestadas (ver pseudocódigo abajo).
Supuestos:
  - (supuesto) Una sola EWM sobre el cierre de BTC (cesta de 1 activo)
  - (supuesto) Señal binaria (+1 largo, -1 corto) — versión simplificada vs Carver continuo
  - EWMAC(32d, 128d) = spans de 768h y 3072h en velas de 1h
  - Entrada al cierre de la vela donde se produce el cruce
  - Sin stop; la salida es el cruce contrario
  - Capital total en posición (no hay fraccionamiento de Carver aquí — se estudia en Fase 07)
Veredicto: APRUEBA
Siguiente paso: Fase 04 Backtest.

### Pseudocódigo completo

```
ENTRADAS:
  precios   = cierre de BTC/USD 1h
  SPAN_F    = 768   (32 dias × 24 horas)
  SPAN_S    = 3072  (128 dias × 24 horas)
  COSTE_RT  = 0.0030  (30 puntos basicos por ida y vuelta = entrada + salida)
  SWAP_L    = 0.000301 por noche en longs
  SWAP_S    = −0.000301 por noche en shorts (ingreso)

SEÑAL:
  EWM_F = media_ewm(precios, span=SPAN_F)
  EWM_S = media_ewm(precios, span=SPAN_S)
  senal  = SI EWM_F > EWM_S → +1 (largo)
           SI EWM_F < EWM_S → −1 (corto)

EJECUCION por vela t:
  posicion_t = senal calculada en vela t−1 (siempre en posicion)
  retorno_bruto_t = posicion_t × retorno_precio_t
  coste_t = SI hubo cambio de señal en t−1 → COSTE_RT / barras_en_posicion
            SINO → 0
  swap_t  = SI posicion_t = +1 → SWAP_L / 24
            SI posicion_t = −1 → SWAP_S / 24
  retorno_neto_t = retorno_bruto_t − coste_t + swap_t

SALIDA:
  curva_equity = producto_acumulado(1 + retorno_neto)
  operaciones  = numero de cruces de señal
  PF   = suma(retornos_positivos) / |suma(retornos_negativos)|
  DD   = max caida desde pico en la curva_equity
```

Supuestos de la fase 03:
- `min_periods = span/2` para evitar NaN en el arranque
- El primer período de calentamiento (~3,072 velas = 128 días) no genera señal
- No hay gestión de riesgo dinámica (se estudia en Fase 07)
- Los costes se distribuyen en las barras que dura la posición (aproximación lineal)

---

## Fase 04 · Backtest · MOTOR

Agente / skill: Director con skill validador-4de4
Qué se hizo: Backtest sobre el periodo de diseño (56%: velas 1–24,547) con costes reales.
Resultado (EWMAC 32d/128d · Long/Short · señal binaria):

  RENDIMIENTO POR AÑO (vs BTC buy-and-hold):
    2022: estrategia +81.1%  vs  BTC −64.6%   ← corto durante el crash
    2023: estrategia +8.0%   vs  BTC +156.0%  ← corto cuando BTC rebotó (pérdida de oportunidad)
    2024: estrategia +26.2%  vs  BTC +39.2%
    Total: +118% en 2.8 años

  CRITERIOS 4/4 (diseño con costes):
    [NO] PF ≥ 1.3       → PF = 1.03  (reparte muchas barras pequeñas entre ganancias y pérdidas)
    [NO] ≥ 30 ops       → 2.5 operaciones/año × 2.8 años = ~7 round-trips
    [NO] DD < 20%       → DD = −45.6%  (equidad cae al quedar corto durante el rally 2023)
    [OK] PF sin mejor   → PF-sin-mejor = 1.03

  VEREDICTO: 1/4 · NO APRUEBA

  POR QUÉ FALLA:
  1. Pocas operaciones: el EWMAC lento hace ~2-3 giros por año → nunca llega a 30 ops en 2.8 años
  2. DD alto: después de ganar +81% en 2022, el sistema se quedó CORTO durante el rebote 2023
     (+156% de BTC) → la equidad cayó 45% desde su pico antes de girar a LARGO
  3. PF bajo: el PF por BARRA es ~1.03 porque cada posición larga tiene muchas barras "planas" o
     mínimamente positivas; el PF "bruto" por operación sería >1 pero el coste lo aplana

Supuestos: datos APTA CON AVISOS · costes 30pb/RT · swap ±0.030%/noche
Veredicto: NO APRUEBA (1/4 — criterio de ops/año y DD son los bloqueantes)
Siguiente paso: Ver opciones de mejora o descartar (ver notas abajo).

---

## NOTAS PARA EL TRADER

### Lo que sí funciona de este sistema
- Capturó el crash de 2022 yendo corto: +81% mientras BTC perdió 65%.
- Ganó dinero en 3 de 4 años (75% años positivos).
- El total de +118% en 2.8 años supera el buy-and-hold del periodo (~0% neto desde oct-2021 a ago-2024).

### Por qué no pasa el filtro TIS
- La lentitud del EWMAC (128 días) hace que el sistema tarde semanas en girar al nuevo trend.
  Durante ese retraso, la equidad cae desde el pico → DD grande.
- El criterio de 30 ops es difícil de cumplir con un sistema que solo hace 2-3 operaciones/año.
  Para 30 ops se necesitarían ~10 años con EWMAC 32d/128d.

### Opciones para mejorar
1. **EWMAC más rápido** (8d/32d): más operaciones (~12/año), pero el DD sube aún más porque el ruido es mayor.
2. **Añadir cesta real**: descargar ETH/USD APTA y construir un índice compuesto BTC+ETH.
   La cesta suaviza el ruido; el EWMAC sobre el índice compuesto puede tener mejor PF.
3. **Stop dinámico**: un stop en, p.ej., −15% del trade limita el DD pero cambia la regla del sistema.
4. **Carver completo con volatility targeting**: la posición se ajusta por volatilidad realizada
   → reduce el tamaño cuando BTC está muy volátil → DD más controlado. Requiere Fase 07.

### Comparación con todas las versiones testeadas (Long/Short binario)

| EWMAC       | Ops/año | PF   | DD      | Años+ | Score |
|-------------|---------|------|---------|-------|-------|
| 2d/8d       |   58.6  | 0.99 | −68.8%  | 75%   | 1/4   |
| 4d/16d      |   26.1  | 1.00 | −61.8%  | 25%   | 1/4   |
| 8d/32d      |   11.8  | 1.01 | −69.9%  | 75%   | 2/4   |
| 16d/64d     |    6.8  | 1.01 | −64.3%  | 50%   | 0/4   |
| **32d/128d**|  **2.5**|**1.03**|**−45.6%**|**100%**|**1/4**|
| 64d/256d    |    0.7  | 1.03 | −54.8%  | 75%   | 1/4   |

Mejor candidato: EWMAC 32d/128d (100% años positivos, menor DD, único con rendimiento real positivo).
