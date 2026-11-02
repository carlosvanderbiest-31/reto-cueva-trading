# pack_datos — pack ligero multiactivo

Armado con `python codigo/armar_pack_datos.py` (se puede regenerar cuando se quiera; borra y rehace esta carpeta).
~234 MB, 174 series. El detalle de cada una (barras, desde, hasta, MB) está en `CATALOGO.csv`.

| Fuente | TF | Series | Qué hay |
|---|---|---|---|
| norgate | D1 | 77 | ETF: índices EE. UU., 10 sectores, 10 industrias, bonos, materias primas, divisas, países, REIT + 22 acciones grandes. Desde 1990 o el alta del ETF. Ajustado por dividendos (TOTALRETURN). |
| darwinex | D1, H1 | 34 + 34 | 14 pares de divisas, 10 índices, oro, plata, petróleo, gas y 6 ETF. Lo que se opera en MT5. H1 desde 2008-2010 (oro desde 1998). |
| darwinex | M5 | 14 | 10 índices + metales + energía. Solo 2024-2026 (MT5 da 100.000 velas como máximo). |
| dukascopy | M5, M15, H1 | 4 × 3 | S&P 500, Nasdaq 100, Dow y Russell 2000, a partir de su 1 minuto. Desde 2011 (Nasdaq) o 2016. |
| dukascopy | H1, H4, D1 | 1 × 3 | Oro desde 2003. |

## Formato
- Un fichero por símbolo y temporalidad: `<fuente>/<TF>/<SIMBOLO>.parquet`.
- Columna de tiempo única: `datetime_servidor` = hora del servidor Darwinex (Nueva York + 7 h). Norgate es diario: la fecha de la sesión.
- Columnas: `open high low close` en todos. Darwinex trae además `tick_volume` y `spread`; el oro de Dukascopy, `tick_volume`. Norgate e índices Dukascopy, sin volumen.

## Avisos
- Darwinex D1 llega a octubre 2026; el H1 de la mayoría y todo el M5 se cortan el 2026-07-31 (última exportación intradía). Norgate y Dukascopy llegan a octubre 2026.
- Comprobado al armarlo: Dukascopy y Darwinex H1 del S&P 500 caen en la misma vela (diferencia mediana 0,05 %, el doble si se desfasa una hora); sin huecos vacíos, sin duplicados, sin high < low.
- `data/` no se versiona: esta carpeta vive solo en este ordenador.
