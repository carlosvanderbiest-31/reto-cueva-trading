# datos/ · Aquí van tus CSV de precios

La cueva no tiene datos de mercado propios. Sin un CSV tuyo, la fase 02 (AED) y la
fase 04 (Backtest) quedan PENDIENTE: es lo correcto, no un error.

## Cómo exportar el CSV desde TradingView
1. Abre TradingView en la computadora (en el celular no se puede exportar).
2. Abre el gráfico del activo (por ejemplo NAS100) y elige la temporalidad (por ejemplo 15 min).
3. Deja el gráfico limpio: sin indicadores (cada indicador añade columnas al archivo).
4. Desplázate hacia la izquierda para cargar todo el historial que quieras: solo se
   exportan las velas que el gráfico tiene cargadas.
5. Menú del gráfico (la flecha junto al nombre del diseño, arriba a la derecha) →
   «Exportar datos del gráfico…» → formato de hora ISO → Exportar.
6. Guarda el archivo en esta carpeta con un nombre claro: `NAS100_15m.csv`.

Ojo: la exportación puede requerir un plan de pago de TradingView, y los planes
gratuitos cargan menos historial. Para años de datos, usa diario o 1 hora.

## Formato del CSV
El CSV tal cual sale de TradingView, sin abrirlo ni guardarlo en Excel (Excel cambia
las comas y las fechas). La primera fila trae los nombres de las columnas:

```
time,open,high,low,close,Volume
2026-01-05T09:30:00-05:00,21500.25,21540.00,21490.50,21530.75,1234
```
- time: fecha y hora de la vela · open: apertura · high: máximo · low: mínimo · close: cierre.
- Volume puede venir o no, según el activo.
- La fila de ejemplo es orientativa: la hora sale con zona horaria (formato ISO) o como
  número (formato UNIX) según lo que elijas al exportar. Elige ISO.
- Comprueba la zona horaria: tu regla dice «apertura de Nueva York» (9:30 hora de Nueva York).

Los CSV no se suben a GitHub (están en .gitignore): son tuyos.
