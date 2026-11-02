---
name: aed
description: Análisis exploratorio de datos (fase 02 del método TIS) — ¿la hipótesis tiene una ventaja estructural o es ruido? Úsala después de aprobar la fase 01.
---
Entrada: la ficha de la hipótesis (fichas/), su PRE-REGISTRO si lo tiene, la ficha técnica
del activo (activos/) si existe, la ficha de pistas de AED CLUES si existe
(resultados/<misma ficha>_pistas.html) y un CSV de precios en datos/ (ver datos/LEEME.md).

0. SI HAY FICHA DE PISTAS DE AED CLUES, esa es tu fuente de números: léela y usa sus casos (n),
   su efecto y su semáforo (clara · se insinúa · nada). No recalcules nada. Respeta su corte:
   los datos reservados no se miran ahora, son para la prueba fuera de muestra de la fase 04.
   Si la pista de la predicción no está en la ficha (por ejemplo, es por hora o por sesión),
   la fase 02 queda PENDIENTE de medición exacta, que se hace con código el Día 3.

1. REVISA LOS DATOS: nº de velas, primera y última fecha, zona horaria y huecos.
   Si la ficha técnica de activos/ avisa de días extremos, confirma con el trader que son reales.
2. CON PRE-REGISTRO, júzgala SOLO contra él:
   - Mide la PREDICCIÓN tal como está escrita (el mismo número, la misma condición).
   - Compárala con la LÍNEA BASE que eligió (todas las velas, el mismo horario sin la señal
     o comprar y mantener). Para la línea base de velas al alza, usa la de activos/ si existe.
   - Mira si se cumplió lo que escribió en «LA DESCARTO SI». Si se cumplió, NO APRUEBA,
     aunque «casi» pase. Nunca cambies el pre-registro, el umbral ni la regla para que pase.
   - Si el trader quiere cambiar algo después de ver el resultado, es una ENMIENDA: va con
     fecha, la anterior se conserva, y la nueva versión se mide con datos que no usó (otros
     años u otro activo).
   SIN PRE-REGISTRO: mide el comportamiento que la hipótesis dice explotar, sin reglas de
   entrada todavía: retorno medio a 1, 5 y 20 velas después de la condición frente a
   cualquier vela, y en cuántos años se cumple.
3. HUELLA: si el pre-registro dice dónde más debería aparecer y hay un segundo CSV, mide la
   misma predicción ahí, sin cambiar nada. Anota si aparece o no.
4. SIN CSV, o si en este computador no puedes ejecutar código: NO inventes ni busques cifras.
   Di qué CSV bajar (activo, temporalidad, años) y cómo (datos/LEEME.md). Veredicto: PENDIENTE.
5. Veredicto: APRUEBA (la predicción supera a la línea base y no se cumplió «la descarto si»:
   pasa a reglas y backtest) · NO APRUEBA (no la supera o se cumplió lo que la tumba: vuelve
   a la hipótesis) · PENDIENTE (faltan datos).
6. Escribe el bloque «Fase 02» con la plantilla metodo/plantillas/FICHA.md. En «Resultado»:
   la predicción medida, la línea base, la diferencia, el nº de casos y la huella si la hubo.
   Con menos de 30 casos, dilo: es una pista, no una conclusión.
Prohibido: dar el veredicto por intuición, sin números; mover la meta del pre-registro.
