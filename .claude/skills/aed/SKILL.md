---
name: aed
description: Análisis exploratorio de datos (fase 02 del método TIS) — ¿la hipótesis tiene una ventaja estructural o es ruido? Úsala después de aprobar la fase 01.
---
Entrada: la hipótesis de la fase 01 y, si lo hay, un CSV de precios en datos/
(TradingView → Exportar datos del gráfico; ver datos/LEEME.md).
1. Revisa los datos: nº de velas, primera y última fecha, huecos.
2. Mide el comportamiento que la hipótesis dice explotar, SIN reglas de entrada todavía:
   ¿qué pasa después de la condición? (retorno medio a 1, 5 y 20 velas frente al retorno
   medio de cualquier vela), ¿en cuántos años se cumple?, ¿se cumple en otros activos parecidos?
3. Sin CSV: NO inventes ni busques cifras. Di qué CSV bajar (activo, temporalidad,
   años), cómo (TradingView en computadora → Exportar datos del gráfico; solo baja las
   velas cargadas: para años, pide diario o 1 hora) y qué número esperarías ver si la
   ventaja existe. Veredicto: PENDIENTE.
4. Veredicto: APRUEBA (hay indicios: pasa a reglas y backtest) · NO APRUEBA (es ruido:
   vuelve a la hipótesis) · PENDIENTE (faltan datos).
5. Escribe el bloque «Fase 02» con la plantilla metodo/plantillas/FICHA.md.
Prohibido: dar el veredicto por intuición, sin números.
