# FICHA · BTC ruptura 30 velas + filtro funding extremo (H6)
Regla: Compro BTCUSDT cuando el cierre 4h supera el máximo de 30 velas Y el funding del par está bajo el percentil 90 histórico (no sobre-apalancado). Salgo a objetivo (2R), stop o 30 velas. Stop: 2×ATR(14). Horario: 24/7, velas 4h.
Por qué funcionaría: funding muy alto = demasiados largos apalancados; evitar esas rupturas quitaría las propensas a long-squeeze. Prima de riesgo de posicionamiento.

## Fase 04 · Backtest · MOTOR
Agente / skill: validador-4de4 (AED fase 02 plegada en el backtest filtrado)
Qué se hizo: motor de ruptura + filtro funding<P90 (gratis: API Binance Futures). 1% riesgo, costes 0,1%/lado, 70/30 sobre 2019-09→2026-10. Código: codigo/btcusdt_ruptura30_filtros.py. P90 calculado solo con el tramo dentro de muestra (sin look-ahead).
Resultado: DENTRO (2019→2024): 159 ops, FB 1,36, caída 8,0%. FUERA (2024→2026): 80 ops, FB 0,85, FB sin mejor 0,81, caída 14,2%.
Supuestos: umbral = percentil 90 del funding dentro de muestra; funding 8h mapeado a la vela 4h.
Veredicto: NO APRUEBA (2/4 fuera de muestra: falla factor de beneficio y FB sin mejor op).
Siguiente paso: descartar; idea nueva con otro comportamiento.
