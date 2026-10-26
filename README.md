# mi-cueva-tis · Monta tu cueva

> **Lo más fácil: haz doble clic en `EMPEZAR`** (Windows: `EMPEZAR.bat` · Mac: `EMPEZAR.command`).
> Se abre la guía visual (`GUIA.html`) y, si ya tienes VS Code, también tu cueva.
> Este archivo es la misma guía en texto, por si la prefieres.

**Hoy montas tu cueva**: un repositorio base con las fases del método TIS y los 4 agentes.
Lo abres en VS Code y tu IA trabaja con un **Director** que conoce el método TIS, **4 agentes** y **3 skills** (manuales de trabajo).
Le das una idea de trading y la pasa por las fases del método, guardándote una **FICHA**.

> La cueva no opera, no da señales y no promete rentabilidad. Ordena tu trabajo para que
> cada idea pase por el método. Tú pones el criterio y decides.

---

## Antes de nada · descomprime
Clic derecho en `mi-cueva-tis.zip` → **Extraer todo…** (en Mac, doble clic). Trabaja siempre
en la carpeta descomprimida, no dentro del ZIP. Ponla donde la encuentres fácil (Documentos).

## Lo que ves en la carpeta
```
mi-cueva-tis/
├─ EMPEZAR.bat / EMPEZAR.command  ← doble clic aquí (Windows / Mac)
├─ GUIA.html                      ← la guía paso a paso
├─ fichas/                        ← aquí se guardan TUS FICHAS (hay un ejemplo de NAS100)
├─ datos/                         ← aquí pondrás tus CSV de precios (lee LEEME.md)
├─ metodo/                        ← el método (METODO.md), la plantilla de ficha y una prueba
└─ AGENTS.md, CLAUDE.md, .claude/, .vscode/  ← NO LOS TOQUES: son el cerebro de tu cueva
```
`AGENTS.md` es el Director; `.claude/` guarda los 4 agentes y las 3 skills; `.vscode/` le dice
a Copilot que lea al Director. Tienen que quedarse donde están.

## Paso 1 · Abre la carpeta en VS Code
Si no tienes VS Code, bájalo gratis de https://code.visualstudio.com/download
```
Archivo → Abrir carpeta…   (en inglés: File → Open Folder…)
   └─ elige la carpeta mi-cueva-tis (la que tiene EMPEZAR y AGENTS.md) → Seleccionar carpeta
```
Si VS Code pregunta «¿Confías en los autores de los archivos de esta carpeta?», responde **Sí, confío**.

## Paso 2 · Activa tu IA (elige UNA opción)

### Opción GRATIS · GitHub Copilot (plan Copilot Free)
Copilot ya viene dentro de VS Code. Solo necesitas una cuenta de GitHub (gratis).
```
Barra de abajo (Status Bar) → icono de Copilot → «Use AI Features»
   └─ inicia sesión con tu cuenta de GitHub y elige el plan Copilot Free
```
Abre el chat: **Ctrl+Alt+I** (en Mac: Ctrl+Cmd+I) → botón **+** para un chat nuevo.
- En el selector de agente elige **Agent** (o directamente **director**). Con «Agent» la IA
  puede crear y editar archivos (tu ficha).
- **Modelo**: en el plan gratis es **«Auto»** (Copilot lo elige solo).
- Copilot lee `AGENTS.md` solo, al empezar cada chat.
- Cuando la IA pida permiso para crear o editar un archivo, revísalo y acepta.
- El plan gratis tiene un límite mensual de uso: si se agota, espera al mes siguiente o usa otra opción.

### Opción DE PAGO · extensión Claude Code
Necesitas una suscripción de pago de Claude (Pro, Max, Team o Enterprise) o una cuenta de Claude Console.
```
Ctrl+Shift+X (Extensiones) → busca «Claude Code» (de Anthropic) → Install
   └─ abre un archivo cualquiera → icono de chispa (Spark), arriba a la derecha → Sign in
```
Claude Code lee `CLAUDE.md` (que remite a `AGENTS.md`), los agentes y las skills solo.

### Alternativa · DeepSeek con la extensión Cline (pagas solo lo que usas)
Necesitas una clave de API de DeepSeek (platform.deepseek.com). La clave es como una
contraseña: no la pegues en ningún archivo de esta carpeta ni la compartas en el grupo.
```
Ctrl+Shift+X → busca «Cline» → Install
   └─ panel de Cline → ⚙️ → API Provider: DeepSeek → pega tu clave → elige el modelo
```
Con Cline, empieza tu primer mensaje con: «Lee AGENTS.md y actúa como el Director.»

## Paso 3 · Tu primer chat con tu cueva
Escribe esto en el chat, cambiando la idea por la tuya (la del Reto 1):
```
Director, esta es mi idea: [PEGA AQUÍ TU IDEA DEL RETO 1]
Pásala por las fases 01 a 03 y guarda la ficha en fichas/
```
Qué esperar:
1. Cada respuesta empieza con «Fase XX · nombre · agente o skill».
2. Te hace **una pregunta cada vez** (máximo 3 por fase). Responde corto.
3. Fase 02 sale **PENDIENTE** si no tienes CSV: es lo correcto. Te dice qué bajar (`datos/LEEME.md`).
4. Fase 03 te devuelve la regla en **pseudocódigo**: pasos numerados, sin código de ninguna plataforma.
5. Guarda la ficha en `fichas/`. Compárala con `fichas/EJEMPLO_nas100_apertura_ny.md`.

¿Quieres ver una conversación completa antes? Abre `metodo/pruebas/primer_chat.md`.

## Paso 4 · Mira tu ficha y entrégala
- Abre tu ficha en la carpeta `fichas/` (panel de la izquierda de VS Code).
- Haz una **captura** y entrégala en el grupo de **MEGA CUEVA** → **3 coins**.
- Compártela en redes etiquetando a **@mariellangsaez** → **+2 coins**.

## ¿Prefieres tu chat? (Claude, ChatGPT o DeepSeek en el navegador)
Camino rápido, sin VS Code: abre `GUIA.html`, sección «¿Prefieres tu chat?», copia el Director
y las skills, pégalos en un chat nuevo y después pega tu orden. La IA no podrá guardar archivos:
te dará la ficha en el chat y tú la guardas en `fichas/`.

## Y después
- **Fase 04**: con tu CSV en `datos/`, pide «Director, pasa a la fase 04». El agente **validador**
  prueba la regla con tus datos y te da el veredicto X/4. El tester de la Cueva lo verás en directo.
- **Haz tuya la cueva**: cambia `metodo/METODO.md` a tu manera. La cueva obedece lo que esté escrito.

## Si algo no va
- **Windows dice «Windows protegió tu PC»** → «Más información» → «Ejecutar de todas formas».
  **Mac dice que no se puede abrir** → clic derecho en `EMPEZAR.command` → Abrir (o Ajustes del
  Sistema → Privacidad y seguridad → «Abrir igualmente»). Si no, abre `GUIA.html` con doble clic.
- **No veo los agentes** → abriste la carpeta equivocada: abre la que tiene `EMPEZAR` y `AGENTS.md`
  (a veces queda `mi-cueva-tis` dentro de otra `mi-cueva-tis`).
- **La IA no actúa como Director** → escribe «Lee AGENTS.md y actúa como el Director».
- **No guarda la ficha** → comprueba que en el chat está elegido **Agent** (no «Ask»).
- **Copilot no responde o dice que se acabó el límite** → revisa que iniciaste sesión con GitHub
  (icono de Copilot abajo); si se agotó el plan gratis, usa «¿Prefieres tu chat?».
