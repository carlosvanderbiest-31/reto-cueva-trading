#!/bin/bash
# CUEVA TIS - Empezar (Mac). Doble clic: abre la guia y, si tienes VS Code, tu cueva.
cd "$(dirname "$0")" || exit 1
CARPETA="$(pwd)"

echo ""
echo "  =============================================="
echo "    CUEVA TIS  -  Trade It Simple"
echo "  =============================================="
echo ""

case "$CARPETA" in
  *AppTranslocation*|/private/var/folders/*)
    echo "  OJO: parece que abriste EMPEZAR desde dentro del ZIP o desde Descargas sin moverla."
    echo "  Si algo falla: mueve la carpeta mi-cueva-tis a Documentos y vuelve a abrir EMPEZAR."
    echo "" ;;
esac

APP=""
if [ -d "/Applications/Visual Studio Code.app" ]; then APP="/Applications/Visual Studio Code.app"
elif [ -d "$HOME/Applications/Visual Studio Code.app" ]; then APP="$HOME/Applications/Visual Studio Code.app"
fi

if [ -n "$APP" ]; then
  echo "window.CUEVA_VSCODE = true;" > "metodo/estado.js" 2>/dev/null
else
  echo "window.CUEVA_VSCODE = false;" > "metodo/estado.js" 2>/dev/null
fi

echo "  [1/2] Abriendo la guia paso a paso (GUIA.html) en tu navegador..."
open "$CARPETA/GUIA.html"

if [ -n "$APP" ]; then
  echo "  [2/2] VS Code encontrado. Abriendo esta carpeta en VS Code..."
  open -a "$APP" "$CARPETA"
else
  echo "  [2/2] No encontre VS Code en esta computadora."
  echo "        Te abro la pagina oficial para descargarlo (es gratis)."
  echo "        Instalalo (arrastralo a Aplicaciones) y vuelve a abrir EMPEZAR."
  open "https://code.visualstudio.com/download"
fi

echo ""
echo "  Listo. Sigue los pasos de la guia en tu navegador."
echo "  Si VS Code pregunta si confias en los autores de la carpeta, responde: Si, confio."
echo "  Puedes cerrar esta ventana."
echo ""
