# El método TIS · tu línea de producción de estrategias

> Edítalo: es TU método. El Director (AGENTS.md) lo sigue tal como esté escrito aquí.

Una estrategia es una línea de producción. Entra una idea; sale **validada** o **descartada**.
Cada fase deja su bloque en la FICHA (`metodo/plantillas/FICHA.md`) con un veredicto:
**APRUEBA**, **NO APRUEBA** o **PENDIENTE** (y qué falta).

## Las 8 fases

| Fase | Qué responde | Tipo | Quién en la cueva |
|---|---|---|---|
| 01 Hipótesis | ¿Qué comportamiento explota y por qué existiría la ventaja? | CRITERIO | agente hipotesis + skill escritor-hipotesis |
| 02 AED | ¿Hay ventaja en los datos o es ruido? (AED = análisis exploratorio de datos) | CRITERIO + DATOS | Director + skill aed |
| 03 Reglas | ¿La regla está escrita sin una sola duda? (pseudocódigo) | MOTOR | agente reglas |
| 04 Backtest | ¿Pasa los 4 números fuera de muestra, con costes? | MOTOR | agente validador + skill validador-4de4 |
| 05 Optimización | ¿Funciona en una meseta de parámetros, no en un pico? | MOTOR | (se construye en el Reto) |
| 06 Robustez | ¿Aguanta costes ×2, Monte Carlo y años malos? | MOTOR | (se construye en el Reto) |
| 07 Tamaño y riesgo | ¿Cuánto riesgo merece? | CRITERIO | tú |
| 08 Puesta en marcha | Demo, servidor, seguimiento | DOCUMENTACIÓN | (se construye en el Reto) |

**Los tres tipos de fase**
- **CRITERIO**: lo decides tú; la IA te ordena las ideas y te pregunta.
- **MOTOR**: lo hace una máquina con datos (la IA con tus datos, un programa).
- **DOCUMENTACIÓN**: dejarlo escrito para poder repetirlo y vigilarlo.

## El Criterio TIS · cuándo aprueba cada fase

| Fase | Aprueba si |
|---|---|
| 01 Hipótesis | La regla tiene activo, entrada, salida, stop y horario medibles, y un porqué escrito (ineficiencia o prima de riesgo). |
| 02 AED | Con un CSV real, el comportamiento aparece de forma clara frente a cualquier vela y se repite en varios años. Sin CSV: PENDIENTE. |
| 03 Reglas | Pseudocódigo completo: dos personas marcarían las mismas operaciones. Supuestos declarados, ninguno «por definir». |
| 04 Backtest | 4/4 en los 4 números (abajo), fuera de muestra y con costes. |
| 05 Optimización | Los parámetros vecinos también funcionan (meseta, no pico). Umbral: se fija en el Reto. |
| 06 Robustez | Sigue cumpliendo con costes ×2, en Monte Carlo y en sus peores años. Umbral: se fija en el Reto. |
| 07 Tamaño y riesgo | Riesgo por operación y caída esperada dentro de lo que el trader acepta. Umbral: se fija en el Reto. |
| 08 Puesta en marcha | Ficha completa, demo, servidor y plan de seguimiento con regla de apagado. Umbral: se fija en el Reto. |

Mientras un umbral diga «se fija en el Reto», esa fase no se puede aprobar: queda PENDIENTE.
Aprobar la fase 04 no hace a una estrategia «validada»: le faltan las fases 05 a 08.

## Los 4 números (fase 04)
Siempre **fuera de muestra** (el 30 % de datos más reciente, que la estrategia no "vio" al
diseñarse) y **con costes**:

1. **Factor de beneficio ≥ 1,3** — lo que ganan las ganadoras ÷ lo que pierden las perdedoras.
2. **Al menos 30 operaciones** — con menos, puede ser suerte.
3. **Caída máxima < 20 %** — la peor bajada desde un máximo de la cuenta.
4. **Factor de beneficio sin la mejor operación > 1** — si sin ella ya no gana, dependía de un golpe de suerte.

Veredicto **X/4**. Solo 4/4 aprueba. **No se bajan nunca** para que algo pase.

## Reglas de la cueva
- Nunca se salta una fase. Nunca se optimiza para que algo pase.
- Sin datos no hay cifras: la fase queda PENDIENTE.
- 70 % de datos para diseñar, 30 % más reciente para juzgar. Sin costes, el resultado no cuenta.
- Lo que no está documentado no existe: cada fase deja su bloque en la ficha.
- La IA no da señales ni promete rentabilidad. Tú pones el criterio y decides.
- Este criterio es una forma de trabajar, no una garantía de rentabilidad.
