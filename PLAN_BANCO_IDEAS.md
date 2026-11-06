# Plan · 5 ideas del Banco de Ideas VIP

Origen: Banco-de-ideas-VIP (10 familias). Probamos 5, en orden, una por sesión, con todas las fases TIS.

| # | Familia | Idea concreta | Mercado · datos | Estado |
|---|---------|---------------|-----------------|--------|
| 1 | Reversión a la media | IBS: cierre en el 20% bajo del rango sobre MA200 | QQQ diario (datos/qqq_1d_yahoo.csv) | NO APRUEBA (3/4 fuera; AED 4/4) |
| 2 | Tendencia y rupturas | Ruptura de máximo de varias semanas | Oro y plata (datos_limpios XAUUSD/XAGUSD D1) | NO APRUEBA (AED: falla en plata, no signif. en oro) |
| 3 | Calendario | Cambio de mes (turn-of-month) | S&P 500 (datos/spy_1d_yahoo.csv) | NO APRUEBA (AED 3/4: falla placebo) |
| 4 | Momentum y rotación | Rotación mensual entre clases de activo | ETFs norgate (SPY,QQQ,GLD,TLT,...) | NO APRUEBA (AED 3/4: falla placebo) |
| 5 | Apertura / ORB | Momentum intradía (1ª media hora → última) | S&P 500 intradía (datos_limpios dukascopy M15) | NO APRUEBA (AED 1/4) |

## Resultado del plan (5/5 probadas)
Las 5 descartadas. Más cerca: #1 QQQ reversión IBS (ventaja real pero factor 1,19 < 1,3). Hallazgos para ideas futuras: ruptura de muy corto plazo (~5 días) en metales; momentum absoluto medido por reducción de caída (no retorno); reversión intradía en el S&P (desvanecer la primera media hora).

Regla del Reto: cada idea pasa 01 Hipótesis → 02 AED → 03 Reglas → 04 Backtest (4 números fuera de muestra). Si NO APRUEBA, se descarta y se registra su ficha. Lo normal es descartar varias.
