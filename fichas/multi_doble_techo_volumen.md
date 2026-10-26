# FICHA · Doble Techo con Divergencia de Volumen
Regla: Vendo cualquier activo líquido con volumen real cuando se forma un segundo máximo (M2) que iguala o supera levemente al primero (M1) pero con volumen menor (<70% del volumen de M1). Salgo al llegar al mínimo del retroceso entre M1 y M2 (salida parcial 50% al 1:1). Stop: 1% por encima del máximo más alto entre M1 y M2. Horario: cualquier sesión, en velas de 1H o 4H.
Por qué funcionaría: El primer máximo reúne compradores con convicción (volumen alto). El segundo intento es FOMO tardío; los vendedores que distribuyeron en M1 ya no recompran, así que la demanda genuina se agotó. Los compradores atrapados en M2, con sus stops colectivos bajo el swing low M1-M2, son el combustible bajista. Ineficiencia conductual — no prima de riesgo.

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: skill hipotesis-trading (escritor-hipotesis)
Qué se hizo: Se convirtió la intuición «segundo máximo con menos volumen → corto» en una regla completa con entrada, salida, stop, tamaño, temporalidad y mecanismo de ventaja.
Resultado: Regla definida. Mercado: activos líquidos con volumen real (BTC/USDT, SPY, NQ, etc.). Temporalidad de señal: 1H o 4H. Confirmación macro: Diario. Entrada: cierre de la vela M2 o ruptura del mínimo de M2 en la vela siguiente. Stop: 1% sobre el máximo de M1/M2. Objetivo: mínimo del retroceso M1-M2, R:R mínimo 1.5:1, salida parcial 50% al 1:1. Tamaño: 1% de cuenta.
Supuestos: (1) «Volumen menor» definido como <70% del volumen de M1. (2) M2 debe igualar o superar M1 para que el escape falso sea válido. (3) El retroceso entre M1 y M2 es de al menos 1.5% para que haya espacio de objetivo. (4) Temporalidad de confirmación macro: Diario. (5) Sin filtro de horario de sesión.
Veredicto: APRUEBA
Siguiente paso: Fase 02 · AED — descargar CSV (activo: BTC/USDT o NQ, temporalidad: 1H o 4H, mínimo 3 años) desde TradingView → Exportar datos del gráfico, y dejarlo en datos/ para medir si el comportamiento post-M2 supera el retorno medio de cualquier vela.

## Fase 03 · Reglas · MOTOR
Agente / skill: agente reglas
Qué se hizo: Se convirtió la regla en pseudocódigo paso a paso sin ninguna ambigüedad. Se identificaron y resolvieron 12 huecos como supuestos declarados.
Resultado: Pseudocódigo completo con 4 estados (BUSCANDO_M1, BUSCANDO_M2, ESPERANDO_RUPTURA, DENTRO), orden de salidas definido, ventana de entrada acotada a 10 velas y manejo del 50/50 de salida.
Supuestos: (1) 4H. (2) Pivote 5v×5v, detección con lag de 5 velas. (3) M1 sin filtro de volumen mínimo. (4) M2 volumen <70% M1. (5) Retroceso mínimo 1.5%. (6) Entrada en ruptura del low de M2. (7) Stop 1% sobre el máximo M1/M2. (8) Objetivo parcial 50% al 1:1. (9) Objetivo final en SWING_LOW. (10) Ventana de 10 velas para la entrada. (11) Stop tiene prioridad si colisiona con objetivo en la misma vela. (12) Máximo 1 operación abierta.
Veredicto: APRUEBA
Siguiente paso: DESCARTADA antes de Fase 04.

## Fase 04 · Backtest · MOTOR
Agente / skill: backtest Python sobre BTCUSDT 4H y 1H + ETHUSDT, SOLUSDT, XRPUSDT, BCHUSDT 1H
Qué se hizo: Backtest en 4H (BTC) y 1H (5 activos). Split 70/30: OOS desde dic 2025.
Resultado: 4H-BTC: 10 trades totales, 0 OOS. 1H-5 activos: 41 trades totales, 0 OOS. El patrón no se formó en el período dic 2025 - oct 2026. Señal demasiado rara para ser validable con este split.
Supuestos: Pivote 5 velas cada lado. Volumen M2 < 70% M1. Retroceso mínimo 1.5%. Ventana entrada 10 velas.
Veredicto: NO APRUEBA — insuficientes operaciones en OOS (0/30 requeridas).
Siguiente paso: Hipótesis descartada. Pasar a H3.

```
DATOS: velas de [activo elegido] en temporalidad 4H (supuesto).
Dirección: solo ventas (cortos). Máximo 1 operación abierta a la vez.
Estado inicial: BUSCANDO_M1.

CADA VELA, al cierre:

— BUSCANDO_M1 —
1. SI el high de esta vela es mayor que los high de las 5 velas anteriores
   Y mayor que los high de las 5 velas siguientes:
     M1        = high de esa vela.
     VOL_M1    = volumen de esa vela.
     SWING_LOW = low de esa vela.
     Estado → BUSCANDO_M2.
   SI NO: no hago nada. FIN de la vela.

— BUSCANDO_M2 —
2. SI el low de esta vela < SWING_LOW:
     SWING_LOW = low de esta vela.
3. SI (M1 − SWING_LOW) / M1 < 0.015:
     no hago nada. FIN de la vela.
4. SI el high de esta vela >= M1
   Y el volumen de esta vela < 0.70 × VOL_M1:
     M2               = high de esta vela.
     NIVEL_ENTRADA    = low de esta vela.
     STOP             = máximo entre M1 y M2, multiplicado por 1.01.
     DISTANCIA        = STOP − NIVEL_ENTRADA.
     OBJETIVO_PARCIAL = NIVEL_ENTRADA − DISTANCIA.
     OBJETIVO_FINAL   = SWING_LOW.
     SALIDA_PARCIAL   = NO.
     VELAS_ESPERANDO  = 0.
     Estado → ESPERANDO_RUPTURA.
   SI NO: no hago nada. FIN de la vela.

— ESPERANDO_RUPTURA —
5. VELAS_ESPERANDO = VELAS_ESPERANDO + 1.
6. SI VELAS_ESPERANDO > 10:
     la configuración venció. Estado → BUSCANDO_M1. FIN de la vela.
7. SI el low de esta vela < NIVEL_ENTRADA:
     VENDE al precio NIVEL_ENTRADA.
     Tamaño: 1% del capital total en riesgo.
     Estado → DENTRO.
   SI NO: no hago nada. FIN de la vela.

— DENTRO —
MIENTRAS esté dentro, en cada vela nueva, en este orden:
  a. SI el high de esta vela >= STOP:
       SALGO con todo lo que quede al precio STOP.
       Estado → BUSCANDO_M1. FIN de la vela.
  b. SI SALIDA_PARCIAL = NO
     Y el low de esta vela <= OBJETIVO_PARCIAL:
       SALGO con el 50% de la posición al precio OBJETIVO_PARCIAL.
       SALIDA_PARCIAL = SÍ.
  c. SI SALIDA_PARCIAL = SÍ
     Y el low de esta vela <= OBJETIVO_FINAL:
       SALGO con el 50% restante al precio OBJETIVO_FINAL.
       Estado → BUSCANDO_M1. FIN de la vela.
  d. SI NO se cumple nada: no hago nada. FIN de la vela.
```
