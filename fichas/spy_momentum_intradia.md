# FICHA · S&P 500 CFD · momentum intradía (idea #5 del Banco de Ideas)
Regla: Trado la última media hora (15:30-16:00 ET) en la dirección de la primera media hora (09:30-10:00 ET). Salida: cierre de sesión. Stop: no aplica (intradía corto; no se llegó a fase 03). Horario: intradía, sesión regular EE.UU.
Por qué funcionaría: parte de los inversores recibe información por la mañana pero no opera hasta el cierre, arrastrando la dirección (familia Apertura/ORB, Banco de Ideas VIP; Gao, Han, Li y Zhou, 2018).

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: hipotesis-trading
Qué se hizo: idea #5 (momentum intradía) en el CFD del S&P 500, M15.
Resultado: señal = signo de la primera media hora; se aplica a la última media hora.
Supuestos: costes 0,01%/lado (CFD índice); datos dukascopy M15.
Veredicto: APRUEBA
Siguiente paso: medir si la primera media hora predice la última (fase 02).

## Fase 02 · AED · CRITERIO + DATOS
Agente / skill: aed
Qué se hizo: retorno de la última media hora en la dirección de la primera, 4 condiciones, 70% más antiguo (2016→2023, 1855 días). Código: codigo/spy_momentum_intradia_aed.py. Verificado y corregido el huso horario: datos en UTC+3 → convertidos a ET (sesión anclada por volatilidad en 09:30 y 08:30).
Resultado: retorno neto −0,018%/día; aciertos de dirección 31,9% (por debajo de 50%); placebo 41,2%; años positivos 2/8.
Supuestos: primera/última media hora = dos barras M15; costes 0,01%/lado; horizonte = última media hora.
Veredicto: NO APRUEBA (1/4: sin ventaja; insinúa reversión intradía, no momentum).
Siguiente paso: descartar. Hallazgo para idea futura: reversión intradía (desvanecer la primera media hora). Plan de 5 ideas completo.
