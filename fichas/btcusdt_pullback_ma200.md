# FICHA · Pullback en tendencia alcista BTC 4H
Regla: Compro BTCUSDT cuando el precio cierra por debajo del mínimo de las 7 velas anteriores Y el precio está por encima de la MA200. Salgo cuando el precio cierra por encima del máximo de las 7 velas anteriores. Stop: 2% por debajo del precio de entrada. Horario: 24/7 (crypto).
Por qué funcionaría: En tendencia alcista (precio > MA200), las roturas cortas del mínimo de 7 velas son trampas bajistas que liquidan stops de manos débiles. Los compradores institucionales y seguidores de tendencia usan esas caídas para acumular. Ineficiencia conductual: el miedo minorista genera el combustible de la recuperación.

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: agente hipotesis + skill escritor-hipotesis
Qué se hizo: Se estructuró la regla verbal en una hipótesis completa con entrada, salida, stop, tamaño y mecanismo.
Resultado: Regla definida. Activo: BTCUSDT. Temporalidad: 4H. Entrada: cierre < mínimo de las 7 velas anteriores Y precio > MA200 (200 períodos). Salida: cierre > máximo de las 7 velas anteriores. Stop: 2% bajo el precio de entrada. Tamaño: 1% del capital en riesgo. Dirección: solo compras (largos).
Supuestos: (1) MA200 = media móvil simple de 200 velas de 4H. (2) «Mínimo de 7 velas» = mínimo más bajo de las 7 velas anteriores, sin contar la vela actual. (3) «Máximo de 7 velas» = máximo más alto de las 7 velas anteriores, sin contar la vela actual. (4) Stop fijo 2% por debajo del precio de entrada. (5) Horario: 24/7. (6) Máximo 1 operación abierta a la vez.
Veredicto: APRUEBA
Siguiente paso: Fase 02 · AED — tenemos BTCUSDT_4h.csv en datos/. Medir retorno medio a 1, 5 y 20 velas después de la condición de entrada vs. retorno medio de cualquier vela.

## Fase 03 · Reglas · MOTOR
Agente / skill: agente reglas
Qué se hizo: Se convirtió la regla en pseudocódigo sin ninguna ambigüedad. Se identificaron y resolvieron 9 huecos como supuestos declarados.
Resultado: Pseudocódigo con 3 estados (BUSCANDO, ENTRADA_PENDIENTE, DENTRO), orden de salidas definido, sin ventana de caducidad (la señal espera exactamente 1 vela para ejecutarse).
Supuestos: (1) MA200 = media simple de los 200 cierres anteriores, sin incluir la vela actual. (2) MIN7 = low más bajo de las 7 velas anteriores, sin incluir la vela actual. (3) MAX7 = high más alto de las 7 velas anteriores, sin incluir la vela actual — se recalcula cada vela mientras se está dentro. (4) Entrada: precio de apertura de la vela siguiente a la señal. (5) Stop fijo: 2% por debajo del precio de compra, no se mueve. (6) Salida: al cierre de la vela que supera MAX7. (7) Si stop y salida se tocan en la misma vela, el stop tiene prioridad. (8) Si hay señal mientras se está dentro, se ignora. (9) Re-entrada permitida si la condición vuelve a cumplirse tras salir.
Veredicto: APRUEBA
Siguiente paso: Fase 04 · Backtest — CSV BTCUSDT_4h.csv disponible en datos/.

```
DATOS: velas de BTCUSDT en 4H.
Dirección: solo compras (largos). Máximo 1 operación abierta a la vez.
Estado inicial: BUSCANDO.

CADA VELA — primero se procesa la apertura, luego el cierre:

A LA APERTURA:
  SI estado = ENTRADA_PENDIENTE:
    PRECIO_COMPRA = apertura de esta vela.
    COMPRA al precio PRECIO_COMPRA.
    STOP = PRECIO_COMPRA × 0.98.
    Tamaño: 1% del capital en riesgo.
    Estado → DENTRO.

AL CIERRE:
  SI estado = DENTRO:
    MAX7 = high más alto de las 7 velas anteriores (sin incluir esta vela).
    a. SI el low de esta vela <= STOP:
         SALGO todo al precio STOP.
         Estado → BUSCANDO. FIN de la vela.
    b. SI el cierre de esta vela > MAX7:
         SALGO todo al cierre de esta vela.
         Estado → BUSCANDO. FIN de la vela.
    c. SI NO se cumple nada: no hago nada. FIN de la vela.

  SI estado = BUSCANDO:
    MA200 = media simple de los 200 cierres anteriores (sin incluir esta vela).
    MIN7  = low más bajo de las 7 velas anteriores (sin incluir esta vela).
    a. SI el cierre de esta vela < MIN7
       Y el cierre de esta vela > MA200:
         Estado → ENTRADA_PENDIENTE.
    b. SI NO: no hago nada. FIN de la vela.
```
