# Pine Script v6 · TradingView

Archivos: robots/<idea>_pine_estrategia.pine y robots/<idea>_pine_indicador.pine
Primera línea siempre: `//@version=6`. Si el trader tiene un script en v5, avisa y escribe en v6.

## Estrategia
```pine
//@version=6
strategy("<idea> · estrategia", overlay = true,
     initial_capital = 10000,
     default_qty_type = strategy.fixed, default_qty_value = 1,
     commission_type = strategy.commission.percent, commission_value = 0.05,  // (supuesto) iguala la fase 04
     slippage = 1,                       // en ticks
     process_orders_on_close = false,    // la orden se llena en la apertura de la vela siguiente
     calc_on_every_tick = false,         // decide solo al cierre de cada vela
     pyramiding = 0)                     // una operación a la vez
```
- **Entrada al cierre o a la apertura.** Por defecto una orden decidida al cierre se llena en la
  apertura de la vela siguiente. Si la regla dice «COMPRA al cierre de hoy», usa
  `process_orders_on_close = true` y márcalo «(supuesto de plataforma)».
- **Órdenes:** `strategy.entry("Compra", strategy.long)` y `strategy.close("Compra")` para
  salidas por condición. Stop y objetivo fijos: `strategy.exit("Salida", "Compra", stop = nivel_stop, limit = nivel_objetivo)`.
  El parámetro `when` ya no existe: usa `if`.
- **Misma vela con stop y objetivo:** TradingView supone un recorrido dentro de la vela (si abre más
  cerca del máximo, va primero al máximo). Escríbelo como supuesto. Con plan Premium o superior se
  puede activar `use_bar_magnifier = true`, que usa velas menores para decidir el orden.
- **Horario:** `en_sesion = not na(time(timeframe.period, "0930-1600", "America/New_York"))`.
  Escribe siempre la zona horaria explícita.

## No mirar el futuro ni redibujar
- Decide con valores de velas cerradas. Con `calc_on_every_tick = false` el script corre al cierre:
  `close`, `high`, `low` son de la vela que acaba de cerrar. `high[1]` es la anterior.
- «Los 5 días anteriores sin contar hoy»: `ta.lowest(low, 5)[1]`.
- **Temporalidad mayor** (por ejemplo, el cierre diario en un gráfico de 1 hora), sin redibujar:
  `cierre_ayer = request.security(syminfo.tickerid, "D", close[1], lookahead = barmerge.lookahead_on)`.
  Nunca `lookahead_on` sin el `[1]`.
- Prohibido: `varip`, `barstate.isrealtime` para cambiar la lógica, `timenow` en las reglas,
  `request.security` sobre otra temporalidad sin la regla de arriba.

## Alertas (para automatizar con webhook)
- En cada orden de la estrategia añade `alert_message`, por ejemplo:
  `strategy.entry("Compra", strategy.long, alert_message = '{"accion":"compra","simbolo":"' + syminfo.ticker + '"}')`.
  El formato exacto del mensaje lo define el puente que recibe la alerta (el servicio que la
  pasa al bróker o a MetaTrader 5). No lo inventes: pregunta qué puente usa y copia el formato
  de su documentación. Si todavía no tiene puente, deja este JSON simple marcado «(supuesto)».
- Al crear la alerta en TradingView, el mensaje es `{{strategy.order.alert_message}}`.
- Los webhooks solo funcionan con plan de pago de TradingView y verificación en dos pasos.

## Indicador
```pine
//@version=6
indicator("<idea> · indicador", overlay = true)
// mismas condiciones que la estrategia, copiadas paso a paso
plotshape(entrada, "Entrada", shape.triangleup, location.belowbar, color.new(color.green, 0), size = size.small)
plotshape(salida, "Salida", shape.xcross, location.abovebar, color.new(color.red, 0), size = size.small)
plot(nivel_stop, "Stop", color.new(color.red, 40), style = plot.style_linebr)
alertcondition(entrada, "Entrada", "Entrada <idea>")
```
- El indicador no sabe si hay una operación abierta como la estrategia. Lleva esa cuenta con una
  variable `var bool dentro = false` que cambia en la entrada y la salida, para no marcar
  entradas repetidas.

## Dónde pegarlo y cómo compilar (para el trader)
1. Abre un gráfico del activo y la temporalidad de la regla.
2. Abajo, pestaña **Pine Editor** → menú del script → **Crear nuevo** (estrategia o indicador).
3. Borra lo que trae, pega el código y pulsa **Guardar**.
4. Pulsa **Añadir al gráfico**. Si hay errores, salen en la consola de abajo con el número de
   línea: cópialos tal cual y pégaselos al agente.
5. Costes: en la estrategia, ⚙ **Configuración** → **Propiedades** (comisión y deslizamiento).
   Resultados: pestaña **Probador de estrategias**.
