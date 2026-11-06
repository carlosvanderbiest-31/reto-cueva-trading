# FICHA · BTC ruptura 30 velas + filtro Coinbase Premium (H7)
Regla: Compro BTCUSDT cuando el cierre 4h supera el máximo de 30 velas Y el Coinbase Premium del día anterior es >0. Salgo a objetivo (2R), stop o 30 velas. Stop: 2×ATR(14). Horario: 24/7, velas 4h.
Por qué funcionaría: el premium de Coinbase refleja compra spot real de EE.UU.; rupturas con premium positivo tendrían comprador estructural. Ventaja de prima de riesgo (momentum con confirmación de flujo spot).

## Fase 04 · Backtest · MOTOR
Agente / skill: validador-4de4 (AED fase 02 plegada en el backtest filtrado)
Qué se hizo: motor de ruptura + filtro premium>0 (datos gratis Coinbase−Binance, datos/btc_premium.csv). 1% riesgo, costes 0,1%/lado, 70/30 sobre 2017-08→2026-10. Código: codigo/btcusdt_ruptura30_filtros.py. Premium con 1 día de retraso (sin look-ahead).
Resultado: DENTRO (2017→2024): 172 ops, FB 1,37, caída 10,1%. FUERA (2024→2026): 59 ops, FB 1,10, FB sin mejor 1,05, caída 9,3%.
Supuestos: premium diario (Coinbase vs Binance close), no 4h; umbral premium>0.
Veredicto: NO APRUEBA (3/4 fuera de muestra: falla factor de beneficio ≥1,3, quedó en 1,10).
Siguiente paso: descartar; no afinar el umbral (sería overfitting). Idea nueva con otro comportamiento.
