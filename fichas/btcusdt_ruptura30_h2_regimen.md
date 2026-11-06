# FICHA · BTC ruptura 30 velas + filtro de régimen F&G + MVRV-Z (H2)
Regla: Compro BTCUSDT cuando el cierre 4h supera el máximo de 30 velas Y Fear&Greed<80 Y MVRV-Z<7. Salgo a objetivo (2R), stop o 30 velas. Stop: 2×ATR(14). Horario: 24/7, velas 4h.
Por qué funcionaría: evitar comprar rupturas en euforia extrema (F&G alto / MVRV caliente = zona de distribución). Mezcla conductual + gestión de cola.

## Fase 04 · Backtest · MOTOR
Agente / skill: validador-4de4 (AED fase 02 plegada en el backtest filtrado)
Qué se hizo: motor de ruptura + filtro F&G<80 y MVRV-Z<7 (gratis: alternative.me y bitcoin-data.com). 1% riesgo, costes 0,1%/lado, 70/30 sobre 2022-11→2026-10 (MVRV limita el inicio). Código: codigo/btcusdt_ruptura30_filtros.py. Series con 1 día de retraso.
Resultado: DENTRO (2022→2025): 105 ops, FB 1,44, caída 8,5%. FUERA (2025→2026): 39 ops, FB 0,60, FB sin mejor 0,53, caída 11,2%.
Supuestos: zona roja MVRV-Z = ≥7; F&G umbral 80. Historial corto por MVRV (desde 2022-11).
Veredicto: NO APRUEBA (2/4 fuera de muestra: falla factor de beneficio y FB sin mejor op).
Siguiente paso: descartar; idea nueva con otro comportamiento.
