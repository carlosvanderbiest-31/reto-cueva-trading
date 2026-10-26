# datos/ · Aquí van tus CSV de precios

La cueva no tiene datos de mercado propios. Sin un CSV tuyo, la fase 02 (AED) y la
fase 04 (Backtest) quedan PENDIENTE: es lo correcto, no un error.

## ¿De dónde saco los datos? Fuentes gratis

**La forma más fácil:** escribe `/datos` en el chat de tu IA. El agente datos te pregunta qué
necesitas, tú eliges la fuente, y él los descarga con Python, los cura y te deja aquí un CSV limpio
con su informe de calidad.

Cualquier CSV de precios sirve: la ficha técnica del Día 2 y tu Director leen los formatos
más comunes. Estas fuentes no piden pago (algunas piden una cuenta gratis):

| Fuente | Sirve para | Cómo |
|---|---|---|
| **Tu MetaTrader 5** | Lo que opera tu bróker: índices, divisas, oro, cripto | Ver → Símbolos → elige el símbolo → pestaña Barras → elige temporalidad y fechas → Solicitar → Exportar barras |
| **Yahoo Finance** | Acciones, ETF, índices y cripto, en diario | Busca el ticker → Historical Data → periodo Max → Download. Si pide iniciar sesión, la cuenta es gratis |
| **Stooq** (stooq.com) | Índices, acciones, ETF, divisas, materias primas y cripto | Diario con muchos años; 1 hora y 5 minutos solo con las últimas velas. Pide un captcha para descargar |
| **Dukascopy** (dukascopy.com → Historical data export) | Divisas, oro, índices y materias primas, también intradía | Elige instrumento, temporalidad y fechas → descarga en CSV. Puede pedir registrarte gratis |
| **TradingView** | Casi todo | Según tu plan, exportar puede pedir una suscripción de pago. Pasos abajo |

**Qué elegir:**
- Para la fase 02 con AED CLUES: **velas diarias**, con todos los años que puedas (5 o más).
- Si tu idea es por hora o por sesión: 1 hora o 15 minutos de **tu MetaTrader** o de **Dukascopy**.
- El Día 3 aprendes a bajarlos con Python, sin depender de ninguna página.

## Cómo exportar el CSV desde TradingView
1. Abre TradingView en la computadora (en el celular no se puede exportar).
2. Abre el gráfico del activo (por ejemplo NAS100) y elige la temporalidad (por ejemplo 15 min).
3. Deja el gráfico limpio: sin indicadores (cada indicador añade columnas al archivo).
4. Desplázate hacia la izquierda para cargar todo el historial que quieras: solo se
   exportan las velas que el gráfico tiene cargadas.
5. Menú del gráfico (la flecha junto al nombre del diseño, arriba a la derecha) →
   «Exportar datos del gráfico…» → formato de hora ISO → Exportar.
6. Guarda el archivo en esta carpeta con un nombre claro: `NAS100_15m.csv`.

Ojo: según tu plan, exportar desde TradingView puede pedir una suscripción de pago, y los
planes gratuitos cargan menos historial. Si no puedes exportar, usa una de las fuentes de arriba.

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
