# FICHA · S&P 500 (SPY) · cambio de mes / turn-of-month (idea #3 del Banco de Ideas)
Regla: Estoy largo en SPY los días TOM (último día de bolsa del mes + primeros 3 del siguiente), flat el resto. Salida/stop: a definir en fase 03 (no se llegó). Horario: diario.
Por qué funcionaría: entradas de dinero recurrentes (nóminas, aportes a fondos) y rebalanceos concentran compras al cambio de mes (familia Calendario, Banco de Ideas VIP; Lakonishok-Smidt, McConnell-Xu).

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: hipotesis-trading
Qué se hizo: idea #3 del banco (cambio de mes) en S&P 500.
Resultado: ventana TOM = {último día del mes, primeros 3 del siguiente}; comportamiento = retorno diario TOM > día cualquiera.
Supuestos: riesgo 1%; costes 0,03%/lado (SPY muy líquido).
Veredicto: APRUEBA
Siguiente paso: medir si el calendario es ventaja o ruido (fase 02).

## Fase 02 · AED · CRITERIO + DATOS
Agente / skill: aed
Qué se hizo: retorno diario en días TOM vs todos, 4 condiciones, 70% más antiguo de spy_1d_yahoo.csv (2000→2018). Código: codigo/spy_turnofmonth_aed.py.
Resultado: TOM 0,0553%/día vs 0,0292% cualquier día (dif +0,026%). Casos 902. Placebo 23,3% (no significativo). Años positivos 12/19.
Supuestos: ventana {último + 3 primeros}; horizonte 1 día declarado antes de medir; costes se cancelan en la diferencia diaria.
Veredicto: NO APRUEBA (3/4: falla placebo; la ventaja no es distinguible del azar).
Siguiente paso: descartar. Consistente con el debilitamiento conocido de los efectos de calendario. Seguir con idea #4 del plan.
