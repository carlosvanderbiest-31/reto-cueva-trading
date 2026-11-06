# FICHA · BTC ruptura 30 velas + filtro flujo de ETF (H4)
Regla: Compro BTCUSDT cuando el cierre 4h supera el máximo de 30 velas Y los ETF spot tuvieron flujo neto positivo en ≥3 de los últimos 5 días hábiles. Salgo a objetivo (2R), stop o 30 velas. Stop: 2×ATR(14). Horario: 24/7, velas 4h.
Por qué funcionaría: flujo de ETF = dinero institucional real empujando el spot; ruptura con comprador estructural detrás.

## Fase 04 · Backtest · MOTOR
Agente / skill: validador-4de4 (AED fase 02 plegada en el backtest filtrado)
Qué se hizo: motor de ruptura + filtro ETF (gratis: bitcoin-data.com, solo desde 2024-01). 1% riesgo, costes 0,1%/lado, 70/30 sobre 2024-01→2026-10. Código: codigo/btcusdt_ruptura30_filtros.py. Flujo con 1 día de retraso.
Resultado: DENTRO (2024→2025): 58 ops, FB 1,14, caída 7,2%. FUERA (2025→2026): 17 ops, FB 0,28, FB sin mejor 0,14, caída 9,6%.
Supuestos: historial corto (ETFs existen desde ene-2024); el 30% fuera de muestra no alcanza 30 operaciones.
Veredicto: NO APRUEBA (1/4 fuera de muestra: falla por pocos casos, factor de beneficio y FB sin mejor op).
Siguiente paso: descartar; idea nueva con otro comportamiento (o re-evaluar H4 en el futuro con más años de ETF).
