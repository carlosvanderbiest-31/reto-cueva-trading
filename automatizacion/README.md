# automatizacion/ · Scripts de operación diaria

Scripts que corren solos en el VPS para mantener la cueva funcionando sin intervención manual.
Cada uno se ejecuta como cron job después de que el mercado cerró o antes de que abre.

## Scripts

### datos_refresh.py
Actualiza los CSVs de activos activos con las velas nuevas del día.

- Lee la lista de activos desde `resultados/estado_cueva.md` (tabla con columna `activo = si`).
  Si el archivo no existe, usa los 5 activos por defecto: BTC, ETH, SOL, XRP, BCH (diario, Yahoo).
- Descarga solo desde la última fecha del CSV hasta hoy (incremental, no descarga desde cero).
- Agrega las velas nuevas sin duplicados y corre `curar.py` para mantener el informe vigente.
- Si falla un activo, continúa con los demás y registra el error en `resultados/alertas.md`.
- Al terminar escribe `resultados/refresh_log.md` con el resumen de la corrida.
- También intenta actualizar BTC 1h desde Alpaca si `alpaca-py` está instalado.

Dependencias: `pip install yfinance pandas` (alpaca-py opcional).

### vigia.py
Revisa el estado de salud de cada robot y genera una bandera de color.

- Lee los logs de operaciones en `robots/logs/*.log` (una línea por operación: fecha,tipo,precio,pnl).
  Si no hay logs, revisa `robots/estado.json` si existe.
- Calcula PnL del día, PnL de la semana y drawdown desde el último máximo.
- Compara contra los límites de `MI_PLAN.md` (o defaults: capital 5000 USD, pérdida diaria 2%, drawdown 15%).
- Genera bandera por robot: VERDE / AMARILLO / ROJO con una línea de razón.
- Guarda el reporte en `resultados/vigia_<fecha>.md`.
- Si hay ROJO, agrega alerta en `resultados/alertas.md`.

Dependencias: `pip install pandas`.

### briefing.py
(Pendiente de construir — Fase 08 del método TIS.)
Generará el resumen diario de la cueva: estado de robots, datos, alertas activas y siguientes pasos.

---

## Cron jobs en el VPS (Linux)

Edita el crontab con `crontab -e` y agrega estas líneas.
Ajusta la ruta `/root/cueva/` a donde tengas la cueva instalada.

```cron
# Cron jobs para la cueva TIS
# Actualizar datos de precios a las 6:00 AM UTC
0 6 * * * /usr/bin/python3 /root/cueva/automatizacion/datos_refresh.py >> /root/cueva/logs/cron_refresh.log 2>&1

# Revisar estado de robots a las 6:30 AM UTC
30 6 * * * /usr/bin/python3 /root/cueva/automatizacion/vigia.py >> /root/cueva/logs/cron_vigia.log 2>&1

# Briefing diario a las 7:00 AM UTC (pendiente)
# 0 7 * * * /usr/bin/python3 /root/cueva/automatizacion/briefing.py >> /root/cueva/logs/cron_briefing.log 2>&1
```

Para ver los logs del cron:
```bash
tail -f /root/cueva/logs/cron_refresh.log
tail -f /root/cueva/logs/cron_vigia.log
```

Para verificar que el cron está activo:
```bash
crontab -l
```

---

## Ejecutar manualmente (Windows o VPS)

```bash
python automatizacion/datos_refresh.py
python automatizacion/vigia.py
```

Desde la raíz de la cueva (`mi-cueva-tis/`).

---

## Alertas

Todos los errores y robots en ROJO se acumulan en `resultados/alertas.md`.
Revisarlo cada mañana antes de operar.
