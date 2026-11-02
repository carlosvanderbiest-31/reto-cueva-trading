---
name: validador-4de4
description: Backtest con costes y veredicto de los 4 números TIS fuera de muestra (fase 04 del método TIS). Úsala cuando la regla ya está en pseudocódigo (fase 03) y hay un CSV de precios en datos/.
---
Entrada: el pseudocódigo de la fase 03 y un CSV de precios en datos/. Si existe su informe de calidad
(resultados/<archivo>_calidad.md), léelo: con NO APTA, no hagas el backtest y propone /datos; con
APTA CON AVISOS, copia los avisos en el bloque de la fase 04.
1. La regla se prueba EXACTAMENTE como está escrita. Si algo es ambiguo, pregunta.
2. Backtest con costes realistas para el activo (di cuáles usas y por qué).
3. 70 % de datos más antiguos = dentro de muestra; 30 % más recientes = fuera de muestra.
4. Tabla con ✓/✕, fuera de muestra: factor de beneficio ≥ 1,3 · ≥ 30 operaciones ·
   caída máxima < 20 % · factor de beneficio sin la mejor operación > 1.
5. Veredicto X/4 (4/4 = APRUEBA). Si falla, di qué número falla y UNA idea para la siguiente hipótesis.
6. Escribe el bloque «Fase 04» con la plantilla metodo/plantillas/FICHA.md.
Si no puedes ejecutar un backtest con el CSV, no estimes nada: la fase queda PENDIENTE,
la regla queda lista en piezas y el backtest con código se monta el Día 3 del Reto (carpeta codigo/).
Prohibido: optimizar parámetros para que pase e inventar o estimar resultados.
