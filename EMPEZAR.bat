@echo off
chcp 65001 >nul
title CUEVA TIS - Empezar
cd /d "%~dp0"
set "CARPETA=%~dp0."
rem Por si se lanza desde otra app basada en Electron: que VS Code arranque normal.
set "ELECTRON_RUN_AS_NODE="

echo.
echo  ==============================================
echo    CUEVA TIS  -  Trade It Simple
echo  ==============================================
echo.

rem --- 1. Comprobar que la carpeta esta descomprimida ---
echo "%~dp0" | findstr /i "\Temp\ \Temporary" >nul
if not errorlevel 1 (
  echo  OJO: parece que abriste EMPEZAR desde dentro del ZIP.
  echo  Cierra esta ventana, haz clic derecho en mi-cueva-tis.zip,
  echo  elige "Extraer todo..." y vuelve a hacer doble clic en EMPEZAR.
  echo.
)

rem --- 2. Buscar VS Code ---
set "VSCODE="
if exist "%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe" set "VSCODE=%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"
if not defined VSCODE if exist "%ProgramFiles%\Microsoft VS Code\Code.exe" set "VSCODE=%ProgramFiles%\Microsoft VS Code\Code.exe"
if not defined VSCODE if exist "%ProgramFiles(x86)%\Microsoft VS Code\Code.exe" set "VSCODE=%ProgramFiles(x86)%\Microsoft VS Code\Code.exe"
set "VSCODE_CMD="
if not defined VSCODE (
  where code >nul 2>nul
  if not errorlevel 1 set "VSCODE_CMD=code"
)

rem --- 3. Avisar a la guia de si hay VS Code (archivo pequeno en cueva\) ---
if defined VSCODE (
  > "metodo\estado.js" echo window.CUEVA_VSCODE = true;
) else if defined VSCODE_CMD (
  > "metodo\estado.js" echo window.CUEVA_VSCODE = true;
) else (
  > "metodo\estado.js" echo window.CUEVA_VSCODE = false;
)

rem --- 4. Abrir la guia ---
echo  [1/2] Abriendo la guia paso a paso (GUIA.html) en tu navegador...
start "" "%~dp0GUIA.html"

rem --- 5. Abrir la carpeta en VS Code o la pagina de descarga ---
if defined VSCODE (
  echo  [2/2] VS Code encontrado. Abriendo esta carpeta en VS Code...
  start "" "%VSCODE%" "%CARPETA%"
  goto fin
)
if defined VSCODE_CMD (
  echo  [2/2] VS Code encontrado. Abriendo esta carpeta en VS Code...
  call code "%CARPETA%"
  goto fin
)
echo  [2/2] No encontre VS Code en esta computadora.
echo        Te abro la pagina oficial para descargarlo (es gratis).
echo        Instalalo, y despues vuelve a hacer doble clic en EMPEZAR.
start "" "https://code.visualstudio.com/download"

:fin
echo.
echo  Listo. Sigue los pasos de la guia en tu navegador.
echo  Si VS Code pregunta si confias en los autores de la carpeta,
echo  responde: Si, confio.
echo.
echo  Puedes cerrar esta ventana.
pause
