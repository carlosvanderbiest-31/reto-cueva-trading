---
name: datos_refresh
description: Actualiza diariamente todos los CSVs de activos activos descargando solo las velas nuevas, corriendo curar.py y escribiendo el log. Úsala cuando el trader escriba /datos_refresh o quiera actualizar datos sin descargar desde cero.
---
Eres el Director de la cueva (AGENTS.md) ejecutando la skill datos_refresh.
Español latino, frases cortas. Esta skill no tiene fases: es operativa.

## Qué hace

Lee la lista de activos activos (desde `resultados/estado_cueva.md` o el default).
Por cada activo descarga solo las velas nuevas —desde la última fecha del CSV hasta hoy—
y las agrega al CSV sin duplicados. Luego corre `curar.py` para mantener el informe de
calidad vigente. Si algo falla, lo registra en `resultados/alertas.md`. Al terminar
escribe `resultados/refresh_log.md` con el resumen de la corrida.

## Cuándo usarla

- Cada mañana antes de correr cualquier robot o análisis.
- Después de agregar un activo nuevo a `resultados/estado_cueva.md`.
- Cuando el trader note que los datos tienen varios días de retraso.

## Cómo correrla

```
python automatizacion/datos_refresh.py
```

O como cron job en el VPS:
```
0 6 * * * /usr/bin/python3 /root/cueva/automatizacion/datos_refresh.py
```

## Activos por defecto (si no existe estado_cueva.md)

| Ticker Yahoo | Archivo CSV destino | Temporalidad | Mercado |
|---|---|---|---|
| BTC-USD | datos/btcusd_1d_yahoo.csv | 1d | cripto |
| ETH-USD | datos/ethusdt_1d_yahoo.csv | 1d | cripto |
| SOL-USD | datos/solusdt_1d_yahoo.csv | 1d | cripto |
| XRP-USD | datos/xrpusdt_1d_yahoo.csv | 1d | cripto |
| BCH-USD | datos/bchusdt_1d_yahoo.csv | 1d | cripto |

Además, si `alpaca-py` está instalado, actualiza `datos/btcusd_1h_alpaca.csv` (BTC 1h).

## Formato de estado_cueva.md (opcional)

El archivo puede tener una tabla con columnas: ticker_yahoo, csv_destino, temporalidad, mercado, activo.
Solo se procesan las filas donde `activo == si` (o `activo == true`).
Si el archivo no existe o no tiene la tabla, se usan los activos por defecto.

## Archivos que escribe

- `resultados/refresh_log.md` — resumen de cada corrida (fecha, activos, velas nuevas)
- `resultados/alertas.md` — errores por activo con timestamp (append)
- `resultados/<activo>_<temporalidad>_<fuente>_calidad.md` — informe actualizado por curar.py

## Errores comunes

- **No hay conexión**: el script falla en la descarga; queda registrado en alertas.md, los demás activos continúan.
- **CSV no existe**: se descarga desde el inicio (últimos 5 años) y se crea el archivo.
- **curar.py no disponible**: se registra aviso en alertas.md pero el CSV actualizado queda igual.

Prohibido: sobrescribir el veredicto de curar.py. Si dice NO APTA, se reporta NO APTA.
