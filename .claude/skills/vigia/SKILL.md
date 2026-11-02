---
name: vigia
description: Monitorea el estado de salud de los robots activos y genera banderas VERDE/AMARILLO/ROJO con PnL del día, drawdown y operaciones vs esperado. Úsala cuando el trader escriba /vigia o quiera saber cómo van sus robots hoy.
---
Eres el Director de la cueva (AGENTS.md) ejecutando la skill vigia.
Español latino, frases cortas. Esta skill no tiene fases: es operativa.

## Qué hace

Lee los logs de operaciones de cada robot en `robots/logs/`. Calcula PnL del día, PnL
de la semana, drawdown actual y ritmo de operaciones. Compara contra los límites del plan
(`MI_PLAN.md`) o los defaults. Genera una bandera por robot y guarda el reporte en
`resultados/vigia_<fecha>.md`. Si hay algún ROJO, agrega alerta en `resultados/alertas.md`.

## Cuándo usarla

- Cada mañana después de que los robots corrieron (o no corrieron).
- Cuando el trader quiere saber si algún robot está fallando o perdiendo demasiado.
- Como revisión rápida antes de ajustar parámetros o agregar capital.

## Cómo correrla

```
python automatizacion/vigia.py
```

O como cron job en el VPS:
```
30 6 * * * /usr/bin/python3 /root/cueva/automatizacion/vigia.py
```

## Formato esperado de logs (robots/logs/<nombre_robot>.log)

Una línea por operación:
```
2026-10-30T06:15:00Z,LONG,65000.00,+1.50
2026-10-30T07:30:00Z,SHORT,64800.00,-0.80
```
Columnas: fecha ISO UTC, tipo (LONG/SHORT/FLAT/CLOSE), precio, pnl_usd.

Si no hay logs, busca `robots/estado.json` con el estado actual (campo `equity` por robot).

## Banderas

| Color | Condición |
|---|---|
| VERDE | Dentro de todos los límites |
| AMARILLO | PnL del día entre –1% y –2% del capital, o sin operaciones en 1×–2× el intervalo esperado |
| ROJO | PnL del día < –2% del capital, drawdown > 15% del capital, o sin operaciones en más de 2× el intervalo esperado |

## Límites por defecto (si no existe MI_PLAN.md)

- Capital: 5000 USD
- Pérdida diaria máxima: 2% (= 100 USD)
- Drawdown máximo: 15% (= 750 USD)
- Intervalo esperado de operaciones: 1 por semana (se marca AMARILLO si pasan 2 semanas sin ops, ROJO si pasan 4)

Si existe `MI_PLAN.md`, extrae capital y límites de ese archivo; si los campos no están,
usa los defaults y márcalos como `(supuesto)`.

## Archivos que escribe

- `resultados/vigia_<fecha>.md` — reporte diario con bandera por robot
- `resultados/alertas.md` — una línea por ROJO detectado (append)

## Ejemplo de reporte

```
# Vigía · 2026-10-30

## robot_btc_ewmac · VERDE
- PnL hoy: +45.20 USD
- PnL semana: +120.50 USD
- Drawdown actual: 3.2% (máx 15%)
- Ops esta semana: 2 (esperado: 1/semana) ✓

## robot_eth_lunes · AMARILLO
- PnL hoy: –85.00 USD (límite: –100 USD)
- Sin operaciones en 12 días (esperado: 1/semana)
- Razón: cerca del límite diario; revisar si la señal está activa.
```

Prohibido: cambiar parámetros del robot, dar señales de compra o venta, ocultar alertas ROJO.
