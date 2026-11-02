# NinjaScript · NinjaTrader 8

Archivos: robots/<idea>_ninjatrader_estrategia.cs y robots/<idea>_ninjatrader_indicador.cs
Lenguaje: C#. El nombre de la clase debe ser igual al nombre del archivo en NinjaTrader.

## Estrategia
```csharp
#region Using declarations
using System;
using System.ComponentModel.DataAnnotations;
using NinjaTrader.Cbi;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class NombreIdeaEstrategia : Strategy
    {
        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "NombreIdeaEstrategia";
                Calculate = Calculate.OnBarClose;        // decide solo al cierre de cada vela
                EntriesPerDirection = 1;                 // una operación a la vez
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = false;    // ¡revisar! si es true cierra todo al final de la sesión
                BarsRequiredToTrade = 20;                // velas mínimas antes de operar
                Slippage = 1;                            // en ticks (supuesto)
            }
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < BarsRequiredToTrade) return;
            // Paso 1 · ...
        }
    }
}
```
- **No mirar el futuro:** con `Calculate.OnBarClose`, `Close[0]` es la vela que ACABA de cerrar y
  `Close[1]` la anterior. Nunca uses `Calculate.OnEachTick` u `OnPriceChange` para decidir: con
  eso `[0]` es la vela que se está formando.
- «Mínimo de los 5 anteriores sin contar la actual»: `MIN(Low, 5)[1]`.
- **Temporalidad mayor:** en `State.Configure` → `AddDataSeries(BarsPeriodType.Day, 1);`.
  En `OnBarUpdate` trabaja solo cuando `BarsInProgress == 0` y lee `Closes[1][0]`, que es la
  última vela diaria cerrada.
- **Entrada:** la orden decidida al cierre se llena en la apertura de la vela siguiente. Si la
  regla dice «al cierre», márcalo «(supuesto de plataforma)».
- **Órdenes:** `EnterLong("Compra")`, `ExitLong("Salida", "Compra")`. Stop fijo:
  `SetStopLoss("Compra", CalculationMode.Price, nivel_stop, false)` ANTES de `EnterLong`, o una
  orden `ExitLongStopMarket` que se vuelve a enviar en cada vela.
- **Cierre al final de la sesión:** `IsExitOnSessionCloseStrategy` cierra todo al final del día.
  Ponlo como dice la regla, nunca lo dejes por defecto sin decirlo.
- **Hora:** `ToTime(Time[0])` da HHmmss en la zona horaria de NinjaTrader (Herramientas →
  Opciones → General). `Time[0]` es la hora de CIERRE de la vela. Escribe la conversión.
- **Costes:** comisión con una plantilla de comisiones de la cuenta (o en el Strategy Analyzer);
  deslizamiento con `Slippage`. Igual que la fase 04.
- **Parámetros:** propiedades públicas con `[NinjaScriptProperty]` y `[Range]`, solo las de la regla.

## Indicador
- Clase en `namespace NinjaTrader.NinjaScript.Indicators`, hereda de `Indicator`,
  `Calculate = Calculate.OnBarClose`, `IsOverlay = true`.
- Marcas: `Draw.ArrowUp(this, "entrada" + CurrentBar, false, 0, Low[0] - 2 * TickSize, Brushes.LimeGreen);`
  y `Draw.ArrowDown(this, "salida" + CurrentBar, false, 0, High[0] + 2 * TickSize, Brushes.Red);`
  (necesita `using System.Windows.Media;` y `using NinjaTrader.NinjaScript.DrawingTools;`).
- Lleva la cuenta de si hay operación abierta para no repetir entradas.
- NinjaTrader añade solo, al compilar, un bloque «NinjaScript generated code» al final del
  indicador. No lo escribas tú.

## Dónde pegarlo y cómo compilar (para el trader)
1. En NinjaTrader: **Nuevo → Editor de NinjaScript**.
2. Clic derecho en la carpeta **Strategies** (o **Indicators**) → **Nueva estrategia** → ponle
   exactamente el nombre de la clase.
3. Borra todo el contenido del archivo, pega el código y pulsa **Compilar** (F5).
4. Los errores salen abajo con archivo, línea y código (por ejemplo CS0103). Cópialos tal cual.
   Ojo: un error en CUALQUIER script de la carpeta impide compilar todos.
5. Para probar: **Nuevo → Strategy Analyzer**, o en el gráfico clic derecho → **Estrategias**,
   añádela y marca **Habilitada**. Siempre en cuenta de simulación.
