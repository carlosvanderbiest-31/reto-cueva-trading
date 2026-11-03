# MI_PLAN.md · Plan del Trader
Generado desde Contrato.pdf · Mega Cueva Tester · 29 octubre 2026

## Mi unidad (contrato firmado)
Opero swing corto en cripto con velas de 4 horas: compro rupturas, durante la sesión y con un robot.
Arriesgo un 1% por operación ($10), acepto rachas de 5 pérdidas y una caída del 20%, y no juzgo
el sistema antes de 30 operaciones (~3.4 años).

## Capital y riesgo
- Capital inicial: $1,000 USD
- Riesgo por operación: 1% = $10
- Caída máxima tolerable: 20% = $200
- Interruptor (revisar todo): caída del 15% desde máximo = $150

## Limites operativos
- Límite semanal: -4% (4 pérdidas, $40) → pauso hasta el lunes
- Límite mensual: -9% (9 pérdidas, $90) → pauso hasta el mes siguiente
- Interruptor: -15% desde máximo → apago el sistema y lo reviso entero

## Horizonte
1. Demo: 6 meses (no llegaré a 30 ops; valido ejecución)
2. Real pequeño: 0.5% por operación ($5) durante 50 operaciones
3. Escalado: hasta 1%, un escalon cada 20 ops dentro de lo esperado

## Mi perfil
- Estilo preferido: comprar fuerza (momentum/rupturas)
- Frecuencia esperada: 8.9 operaciones al año
- Tiempo disponible: mas de 2 h al dia, con robot
- Objetivo: hacer crecer el capital
- Familia que encaja: Ruptura de canal, Momentum de serie temporal

## Revisión de estrategias
- Cada 20 operaciones (~2.3 años), no por sensaciones
- Comparo con backtest: acierto (70%), pérdida media y caída
- Entre revisiones no toco nada

## Para el Director (como usar este plan)
- Si una estrategia propuesta no compra fuerza o rompe el horizonte swing 4H, avisarme en Fase 01
- Si el DD del backtest, llevado al 1% de riesgo, supera el 20%, rechazarla en Fase 04
- En Fase 07: usar capital $1,000 y limite de caída 20% ($200) para sizing
- QQQ (~$500) y activos caros: señalar que requieren fractional shares o CFDs
