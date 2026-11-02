# MQL5 · MetaTrader 5

Archivos: robots/<idea>_mt5_estrategia.mq5 (Asesor Experto, EA) y robots/<idea>_mt5_indicador.mq5
Los compilados (.ex5) no se suben a GitHub.

## Estrategia (Asesor Experto)
Estructura mínima:
```mql5
#include <Trade\Trade.mqh>
CTrade trade;

input double lotes        = 0.10;   // tamaño (de la ficha o supuesto)
input long   numero_magico = 20261;  // identifica las operaciones de este robot
input int    desfase_horas = 0;     // hora del servidor del bróker − hora de la regla (supuesto de plataforma)

int OnInit() { trade.SetExpertMagicNumber(numero_magico); return INIT_SUCCEEDED; }

void OnTick()
{
   // Decide solo una vez por vela, cuando la anterior acaba de cerrar
   static datetime ultima_vela = 0;
   datetime vela_actual = iTime(_Symbol, _Period, 0);
   if(vela_actual == ultima_vela) return;
   ultima_vela = vela_actual;

   // A partir de aquí: la vela cerrada es el índice 1
   double cierre = iClose(_Symbol, _Period, 1);
   // Paso 1 · ...
}
```
- **No mirar el futuro:** el índice 0 es la vela que se está formando. Nunca la uses para decidir.
  Usa el índice 1 (la que acaba de cerrar) y hacia atrás. «Mínimo de los 5 días anteriores sin
  contar hoy»: `iLowest(_Symbol, PERIOD_D1, MODE_LOW, 5, 1)`.
- **Indicadores:** crea el «handle» en `OnInit` (por ejemplo `iMA(...)`) y lee con
  `CopyBuffer(handle, 0, 1, n, buffer)` empezando en 1. Comprueba que `CopyBuffer` devolvió datos.
- **Temporalidad mayor:** `iClose(_Symbol, PERIOD_D1, 1)` es el cierre diario de ayer, ya cerrado.
- **Entrada:** la orden sale en la apertura de la vela nueva (se ejecuta en `OnTick` de la
  primera vela tras el cierre). Si la regla dice «al cierre», es lo más cercano posible en
  MetaTrader 5: márcalo «(supuesto de plataforma)».
- **Órdenes:** `trade.Buy(lotes, _Symbol, 0, stop, objetivo)`; cerrar: `trade.PositionClose(ticket)`.
  Precios normalizados con `NormalizeDouble(precio, _Digits)`. Respeta la distancia mínima del
  bróker (`SYMBOL_TRADE_STOPS_LEVEL`); si el stop de la regla es menor, avisa, no lo cambies.
- **Una operación a la vez:** antes de entrar recorre las posiciones (`PositionsTotal`,
  `PositionGetTicket`) y cuenta solo las de este símbolo y este `numero_magico`.
- **Hora:** `TimeCurrent()` es la hora del SERVIDOR del bróker, que suele ser distinta de la de
  la regla. Convierte con `desfase_horas` y escribe el valor que usaste. Ojo con el cambio de
  horario de verano (marzo y noviembre): dilo en los supuestos.
- **Cuentas de cobertura (hedging) y de compensación (netting):** el código debe funcionar en las
  dos. Gestiona las posiciones por ticket y número mágico.
- **Costes:** el probador usa el spread del historial del bróker. La comisión depende de la
  configuración del símbolo en el bróker: pide al trader que revise en el informe del probador
  que aparece. Si no aparece, dilo en los supuestos.

## Indicador
```mql5
#property indicator_chart_window
#property indicator_buffers 2
#property indicator_plots   2
#property indicator_type1   DRAW_ARROW
#property indicator_color1  clrLimeGreen
#property indicator_label1  "Entrada"
#property indicator_type2   DRAW_ARROW
#property indicator_color2  clrRed
#property indicator_label2  "Salida"
double entradas[], salidas[];
int OnInit()
{
   SetIndexBuffer(0, entradas, INDICATOR_DATA); PlotIndexSetInteger(0, PLOT_ARROW, 233);
   SetIndexBuffer(1, salidas,  INDICATOR_DATA); PlotIndexSetInteger(1, PLOT_ARROW, 234);
   PlotIndexSetDouble(0, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   PlotIndexSetDouble(1, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   return INIT_SUCCEEDED;
}
```
- En `OnCalculate` recorre solo velas cerradas (no marques la vela actual, `rates_total - 1`).
- Lleva la cuenta de si hay operación abierta, igual que la estrategia, para no repetir entradas.

## Dónde pegarlo y cómo compilar (para el trader)
1. En MetaTrader 5: **Herramientas → MetaQuotes Language Editor** (o F4).
2. **Archivo → Nuevo → Asesor Experto (plantilla)** para la estrategia, o **Indicador personalizado**
   para el indicador. Ponle el nombre de la ficha y termina el asistente.
3. Borra todo lo que trae el archivo, pega el código y pulsa **Compilar**.
4. Los errores salen abajo, en **Caja de herramientas → Errores**, con la línea. Cópialos tal cual.
5. En MetaTrader 5: **Navegador → Asesores Expertos**, arrastra el robot al gráfico y activa
   **Trading algorítmico**. Para probarlo: **Ver → Probador de estrategias**, modelo
   «Cada tick basado en ticks reales». Siempre en cuenta demo.
