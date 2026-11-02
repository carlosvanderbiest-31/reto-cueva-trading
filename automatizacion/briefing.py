"""
briefing.py · Reporte diario de la cueva TIS
Corre solo o como cron job: python automatizacion/briefing.py

Lee:
  resultados/estado_cueva.md
  resultados/alertas.md        (opcional)
  robots/*.md y robots/*.txt   (opcional)

Escribe:
  resultados/briefing_AAAA-MM-DD.md

No necesita Internet ni claves. Solo lee archivos de la cueva.
"""

import os
import glob
from datetime import date
from pathlib import Path

# Raíz del proyecto: la carpeta que contiene este script está en automatizacion/,
# así que la raíz es su carpeta padre.
ROOT = Path(__file__).resolve().parent.parent


def leer_archivo(ruta: Path) -> str:
    """Devuelve el contenido del archivo o cadena vacía si no existe."""
    try:
        return ruta.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def contar_estrategias(estado: str) -> tuple[int, int]:
    """Cuenta estrategias en proceso y esperando aprobación desde estado_cueva.md."""
    en_proceso = 0
    esperando = 0
    for linea in estado.splitlines():
        linea = linea.strip()
        if linea.startswith("Estado:"):
            if "AVANZA" in linea:
                en_proceso += 1
            elif "ESPERA APROBACIÓN" in linea:
                en_proceso += 1
                esperando += 1
    return en_proceso, esperando


def contar_robots(estado: str) -> int:
    """Extrae el número de estrategias activas del encabezado de estado_cueva.md."""
    for linea in estado.splitlines():
        if "Estrategias activas:" in linea:
            partes = linea.split(":")
            if len(partes) >= 2:
                try:
                    return int(partes[1].strip())
                except ValueError:
                    pass
    return 0


def detectar_robots_activos() -> list[str]:
    """Busca archivos en robots/ que indiquen robots corriendo."""
    patron = str(ROOT / "robots" / "*")
    archivos = [
        Path(f) for f in glob.glob(patron)
        if Path(f).suffix in (".md", ".txt") and Path(f).name != "LEEME.md"
    ]
    return [f.name for f in archivos]


def semaforo(estado: str, alertas: str, robots_activos: list[str]) -> str:
    """Devuelve VERDE, AMARILLO o ROJO."""
    texto_alerta = alertas.strip().lower()

    # Rojo: alerta crítica explícita
    if any(p in texto_alerta for p in ["crítica", "critica", "caída", "caida", "error", "rojo"]):
        return "ROJO"

    # Amarillo: hay alertas menores o datos faltantes
    if texto_alerta and texto_alerta not in ("", "ninguna"):
        return "AMARILLO"

    if "FALTA" in estado:
        return "AMARILLO"

    if "BLOQUEADA" in estado:
        return "AMARILLO"

    return "VERDE"


def aviso_datos(estado: str) -> str:
    """Devuelve 'OK' o 'AVISO: <activo>' según estado_cueva.md."""
    activos_faltantes = []
    for linea in estado.splitlines():
        if linea.strip().startswith("Datos:") and "FALTA" in linea:
            # Ejemplo: "Datos: FALTA btcusd_1h_alpaca.csv"
            partes = linea.split("FALTA", 1)
            if len(partes) == 2:
                activos_faltantes.append(partes[1].strip())
    if activos_faltantes:
        return "AVISO: " + ", ".join(activos_faltantes)
    return "OK"


def hoy_decides(estado: str) -> str:
    """Extrae la primera tarjeta pendiente del estado_cueva.md."""
    en_tarjetas = False
    for linea in estado.splitlines():
        if "## Tarjetas generadas" in linea:
            en_tarjetas = True
            continue
        if en_tarjetas:
            linea = linea.strip()
            if linea and not linea.startswith("#"):
                # Elimina numeración tipo "1. " al inicio
                if linea[0].isdigit() and ". " in linea:
                    linea = linea.split(". ", 1)[1]
                return linea
    return "revisar el estado con /orquestador"


def resumen_alerta(alertas: str) -> str:
    """Primera línea no vacía de alertas.md, o 'ninguna'."""
    for linea in alertas.splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            return linea
    return "ninguna"


def generar_briefing() -> str:
    """Lee los archivos y arma el texto del briefing."""
    hoy = date.today().strftime("%d/%m/%Y")
    hoy_archivo = date.today().strftime("%Y-%m-%d")

    estado = leer_archivo(ROOT / "resultados" / "estado_cueva.md")
    alertas = leer_archivo(ROOT / "resultados" / "alertas.md")
    robots_activos = detectar_robots_activos()

    # Si no hay estado, el briefing no puede ser útil
    if not estado:
        texto = (
            f"BRIEFING · {hoy}\n\n"
            "ROBOTS ACTIVOS: ? | Estado: ?\n"
            "PIPELINE:       ? estrategias en proceso | ? esperando aprobación\n"
            "DATOS:          ?\n"
            "ALERTA:         ninguna\n\n"
            "HOY DECIDES:    correr /orquestador primero — falta resultados/estado_cueva.md\n"
        )
        return texto, hoy_archivo

    n_robots = contar_robots(estado)
    n_en_proceso, n_esperando = contar_estrategias(estado)
    color = semaforo(estado, alertas, robots_activos)
    datos_aviso = aviso_datos(estado)
    alerta_texto = resumen_alerta(alertas)
    decision = hoy_decides(estado)

    robots_linea = (
        f"{n_robots} robot{'s' if n_robots != 1 else ''} activo{'s' if n_robots != 1 else ''}"
        if n_robots > 0
        else "0 robots · cueva en construcción"
    )

    texto = (
        f"BRIEFING · {hoy}\n\n"
        f"ROBOTS ACTIVOS: {robots_linea} | Estado: {color}\n"
        f"PIPELINE:       {n_en_proceso} estrategia{'s' if n_en_proceso != 1 else ''} en proceso"
        f" | {n_esperando} esperando aprobación\n"
        f"DATOS:          {datos_aviso}\n"
        f"ALERTA:         {alerta_texto}\n\n"
        f"HOY DECIDES:    {decision}\n"
    )

    return texto, hoy_archivo


def main():
    texto, hoy_archivo = generar_briefing()

    salida = ROOT / "resultados" / f"briefing_{hoy_archivo}.md"
    salida.write_text(texto, encoding="utf-8")

    print(texto)
    print(f"[guardado en resultados/briefing_{hoy_archivo}.md]")


if __name__ == "__main__":
    main()
