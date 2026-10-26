# EasyLanguage (TradeStation) · PowerLanguage (MultiCharts)

Los dos lenguajes son casi iguales: el mismo código suele servir en las dos plataformas.
Igual se entregan por separado, porque cambian los menús y algunos detalles.

Archivos:
- TradeStation: robots/<idea>_tradestation_estrategia.txt y robots/<idea>_tradestation_indicador.txt
- MultiCharts: robots/<idea>_multicharts_estrategia.txt y robots/<idea>_multicharts_indicador.txt
(Es texto para pegar en el editor. TradeStation exporta .eld y MultiCharts .pla: no hace falta.)

En MultiCharts las estrategias se llaman **Signals**. En TradeStation, **Strategies**.

## Estrategia
```
{ <idea> · estrategia · generado desde la fase 03
  Supuestos: ... }

[IntrabarOrderGeneration = false]   { decide solo al cierre de cada vela }

Inputs:
    Periodo(5);                       { solo los números de la regla }

Vars:
    Minimo5(0), NivelStop(0);

{ Paso 1 · mínimo de los 5 anteriores, sin contar la vela actual }
Minimo5 = Lowest(Low, Periodo)[1];

{ Paso 2 · entrada }
If MarketPosition = 0 and Close < Minimo5 then
    Buy ("Compra") next bar at market;

{ Paso 3 · salida }
If MarketPosition = 1 and Close > Close[1] then
    Sell ("Salida") next bar at market;
```
- **No mirar el futuro:** el código corre al cierre de cada vela; `Close`, `High` y `Low` son de la
  vela que acaba de cerrar. Nunca uses `Open next bar` ni `High next bar` en una condición.
- **Entrada:** `next bar at market` entra en la apertura de la vela siguiente (lo realista).
  `this bar on close` entra al cierre de la vela que decide: úsalo solo si la regla dice
  «al cierre» y márcalo «(supuesto de plataforma)».
- **Stop:** una orden de stop que se envía en cada vela mientras se está dentro:
  `If MarketPosition = 1 then Sell ("Stop") next bar at NivelStop stop;`
  `SetStopLoss` trabaja en dinero por posición, no en precio: no lo uses si la regla da un precio.
- **Ventas:** `SellShort ("Venta") next bar at market;` y `BuyToCover ("Cubre") next bar at market;`
- **Una operación a la vez:** comprueba `MarketPosition = 0` antes de entrar. En Propiedades,
  deja la piramidación desactivada.
- **Temporalidad mayor:** agrega el mismo símbolo como Data2 en el gráfico. `Close of Data2` es
  la última vela de Data2 ya cerrada. Si la regla dice «ayer», compruébalo una vez con
  `Print(Date, " ", Time, " ", Close of Data2);` antes de confiar.
- **Hora:** `Time` es HHMM (la hora de CIERRE de la vela) en la zona horaria del gráfico (de la
  bolsa o local, según la configuración). `Date` tiene formato 1AAMMDD. Escribe la conversión.
- **Velas necesarias:** el «número máximo de velas que el estudio referencia» (MaxBarsBack) debe
  ser mayor que el periodo más largo de la regla.

## Indicador
```
Inputs: Periodo(5);
Vars: Minimo5(0), Dentro(false);
Minimo5 = Lowest(Low, Periodo)[1];
If Dentro = false and Close < Minimo5 then begin
    Plot1(Low, "Entrada");  Dentro = true;
end else NoPlot(1);
If Dentro and Close > Close[1] then begin
    Plot2(High, "Salida");  Dentro = false;
end else NoPlot(2);
```
- En las propiedades del indicador pon los plots como puntos o flechas, no como línea.
- `Dentro` copia la lógica de posición de la estrategia para no repetir entradas.

## Dónde pegarlo y cómo compilar · TradeStation
1. Abre **TradeStation Development Environment** (TDE).
2. **Archivo → Nuevo → Strategy** (o **Indicator**) con el nombre de la ficha.
3. Pega el código y pulsa **Verify** (verificar). Los errores salen abajo con la línea.
4. En el gráfico: **Insertar → Estrategia** (o Indicador) y elige la tuya.
5. Costes: **Formato → Estrategias → Propiedades para todas → Costes** (comisión y deslizamiento).
   Resultados: **Strategy Performance Report**. Siempre en simulación.

## Dónde pegarlo y cómo compilar · MultiCharts
1. Abre **PowerLanguage Editor**.
2. **Archivo → Nuevo → Signal** (o **Indicator**) con el nombre de la ficha.
3. Pega el código y pulsa **Compilar**. Los errores salen abajo con la línea.
4. En el gráfico: **Insertar → Estrategia** (o Indicador), añade la señal.
5. Costes: **Formato → Propiedades de la estrategia** (comisión y deslizamiento).
   Resultados: **Ver → Informe de rendimiento de la estrategia**. Siempre en simulación.
