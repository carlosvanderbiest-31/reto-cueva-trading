# FICHA · Rotación mensual por momentum entre clases de activo (idea #4 del Banco de Ideas)
Regla: Cada fin de mes me quedo con la clase (SPY/QQQ/EFA/TLT/GLD/VNQ) de mayor momentum a 12 meses; si ninguna supera a los bonos, voy a bonos (IEF). Salida/stop: rotación mensual (no se llegó a fase 03). Horario: mensual.
Por qué funcionaría: el capital persigue lo que sube y el momentum persiste entre clases de activo (familia Momentum y rotación, Banco de Ideas VIP; Antonacci dual momentum, Hoffstein-Faber-Braun).

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: hipotesis-trading
Qué se hizo: idea #4 (rotación por momentum) con 6 clases + bonos como refugio.
Resultado: entrada = clase de mayor momentum 12m; filtro absoluto = bonos si nada supera a los bonos.
Supuestos: riesgo a nivel cartera; costes en rotación (fase 04); precios asumidos ajustados por dividendos.
Veredicto: APRUEBA
Siguiente paso: medir si elegir por momentum es ventaja o ruido (fase 02).

## Fase 02 · AED · CRITERIO + DATOS
Agente / skill: aed
Qué se hizo: retorno del mes siguiente de la clase elegida por momentum vs promedio de las 6 y vs elegir al azar, 4 condiciones, 70% más antiguo (2005-11→2020-05, 175 meses). Código: codigo/rotacion_momentum_aed.py. Datos norgate.
Resultado: momentum 0,826%/mes vs promedio 0,783% = +0,043%. Casos 251. Placebo (elección al azar) 43,7%. Años positivos 12/15.
Supuestos: momentum 12 meses; horizonte 1 mes; precios asumidos ajustados por dividendos (si no, subestima TLT/VNQ).
Veredicto: NO APRUEBA (3/4: falla placebo; la selección relativa no se distingue del azar).
Siguiente paso: descartar la selección relativa. Reformulación futura: medir el momentum ABSOLUTO por su reducción de caída, no por retorno medio. Seguir con idea #5.
