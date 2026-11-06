# FICHA · Oro y plata · ruptura de máximo de 50 días (idea #2 del Banco de Ideas)
Regla: Compro oro/plata cuando el cierre supera el máximo de los últimos 50 días (~10 semanas). Salida/stop: a definir en fase 03 (no se llegó). Horario: diario.
Por qué funcionaría: las tendencias se alimentan de flujos lentos; romper un máximo de varias semanas atraería continuación (familia Tendencia y rupturas, Banco de Ideas VIP; Moskowitz, Ooi y Pedersen, 2012).

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: hipotesis-trading
Qué se hizo: idea #2 del banco (ruptura de varias semanas) en oro y plata.
Resultado: entrada = close > máximo de 50 días; se exige que funcione en ambos metales (descarte si solo en uno).
Supuestos: riesgo 1%; costes 0,05%/lado (CFD metal).
Veredicto: APRUEBA
Siguiente paso: medir si la ruptura es ventaja o ruido (fase 02).

## Fase 02 · AED · CRITERIO + DATOS
Agente / skill: aed
Qué se hizo: retorno forward tras ruptura de 50 días vs cualquier día, 4 condiciones, 70% más antiguo de XAUUSD (1998→2018) y XAGUSD (2002→2019). Código: codigo/metales_ruptura_aed.py.
Resultado: ORO H=20 → señal +0,68% vs base +0,57% = +0,11%; placebo 33,5%; años 9/15 → 3/4. PLATA H=20 → señal −0,09% vs base +0,79% = −0,88%; placebo 94,5% → 1/4. Contexto: a H=5 ambos positivos (oro +0,35%, plata +0,27% sobre base); a H=60 ambos negativos.
Supuestos: costes 0,05%/lado; horizonte 20 días declarado antes de medir.
Veredicto: NO APRUEBA (falla en plata y no es significativa en oro; incumple "en ambos metales").
Siguiente paso: descartar. Hallazgo para idea futura: ruptura de muy corto plazo (~5 días) en metales. Seguir con idea #3 del plan.
