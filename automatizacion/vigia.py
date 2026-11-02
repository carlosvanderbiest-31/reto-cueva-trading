"""
vigia.py · Cueva TIS
Monitorea el estado de salud de los robots activos y genera banderas VERDE/AMARILLO/ROJO.
Cron: 30 6 * * * /usr/bin/python3 /root/cueva/automatizacion/vigia.py
"""
import json
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
ROBOTS_LOGS = BASE / "robots" / "logs"
ROBOTS_ESTADO = BASE / "robots" / "estado.json"
MI_PLAN = BASE / "MI_PLAN.md"
RESULTADOS = BASE / "resultados"
ALERTAS = RESULTADOS / "alertas.md"

CAPITAL_DEFAULT = 5000.0
LIMITE_DIARIO_PCT = 0.02
LIMITE_DRAWDOWN_PCT = 0.15
INTERVALO_ESPERADO_DIAS = 7
AMARILLO_SIN_OPS_X = 2
ROJO_SIN_OPS_X = 4


def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def escribir_alerta(robot, mensaje):
    ALERTAS.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTAS, "a", encoding="utf-8") as f:
        f.write(f"- {ts()} · {robot} · ROJO · {mensaje}\n")


def leer_plan():
    capital = CAPITAL_DEFAULT
    limite_diario = capital * LIMITE_DIARIO_PCT
    limite_dd = capital * LIMITE_DRAWDOWN_PCT
    supuesto = True

    if MI_PLAN.exists():
        texto = MI_PLAN.read_text(encoding="utf-8")
        for linea in texto.splitlines():
            l = linea.lower()
            if "capital" in l:
                for token in linea.split():
                    token_limpio = token.replace(",", "").replace("$", "").replace("USD", "").strip()
                    try:
                        val = float(token_limpio)
                        if val > 100:
                            capital = val
                            supuesto = False
                            break
                    except ValueError:
                        continue
        limite_diario = capital * LIMITE_DIARIO_PCT
        limite_dd = capital * LIMITE_DRAWDOWN_PCT

    return {
        "capital": capital,
        "limite_diario_usd": limite_diario,
        "limite_drawdown_usd": limite_dd,
        "supuesto": supuesto,
    }


def leer_log_robot(ruta_log):
    columnas = ["fecha", "tipo", "precio", "pnl"]
    filas = []
    try:
        with open(ruta_log, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("#"):
                    continue
                partes = [p.strip() for p in linea.split(",")]
                if len(partes) < 4:
                    continue
                try:
                    fecha = pd.to_datetime(partes[0], utc=True)
                    tipo = partes[1]
                    precio = float(partes[2])
                    pnl = float(partes[3])
                    filas.append({"fecha": fecha, "tipo": tipo, "precio": precio, "pnl": pnl})
                except (ValueError, IndexError):
                    continue
    except Exception:
        return pd.DataFrame(columns=columnas)

    if not filas:
        return pd.DataFrame(columns=columnas)
    return pd.DataFrame(filas)


def calcular_drawdown(pnl_acumulado):
    equity = pnl_acumulado.cumsum()
    maximo = equity.cummax()
    dd = (equity - maximo)
    return float(dd.min()) if len(dd) else 0.0


def evaluar_robot(nombre, df, plan, hoy):
    ahora = datetime.now(timezone.utc)
    inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_semana = inicio_hoy - timedelta(days=ahora.weekday())

    if df.empty:
        dias_sin_ops = None
        pnl_hoy = 0.0
        pnl_semana = 0.0
        dd_actual = 0.0
        ops_semana = 0
    else:
        df_hoy = df[df["fecha"] >= inicio_hoy]
        df_semana = df[df["fecha"] >= inicio_semana]
        pnl_hoy = float(df_hoy["pnl"].sum())
        pnl_semana = float(df_semana["pnl"].sum())
        dd_actual = calcular_drawdown(df["pnl"])
        ops_semana = len(df_semana)
        ultima_op = df["fecha"].max()
        dias_sin_ops = (ahora - ultima_op).days

    capital = plan["capital"]
    limite_diario = plan["limite_diario_usd"]
    limite_dd = plan["limite_drawdown_usd"]
    dd_pct = abs(dd_actual) / capital * 100 if capital > 0 else 0.0

    bandera = "VERDE"
    razones = []

    if pnl_hoy < -limite_diario:
        bandera = "ROJO"
        razones.append(f"pérdida diaria {pnl_hoy:.2f} USD supera límite de –{limite_diario:.0f} USD")
    elif pnl_hoy < -limite_diario * 0.5:
        if bandera == "VERDE":
            bandera = "AMARILLO"
        razones.append(f"pérdida diaria {pnl_hoy:.2f} USD cerca del límite (–{limite_diario:.0f} USD)")

    if abs(dd_actual) > limite_dd:
        bandera = "ROJO"
        razones.append(f"drawdown {dd_pct:.1f}% supera límite de {LIMITE_DRAWDOWN_PCT*100:.0f}%")
    elif abs(dd_actual) > limite_dd * 0.7:
        if bandera == "VERDE":
            bandera = "AMARILLO"
        razones.append(f"drawdown {dd_pct:.1f}% acercándose al límite ({LIMITE_DRAWDOWN_PCT*100:.0f}%)")

    if dias_sin_ops is not None:
        umbral_amarillo = INTERVALO_ESPERADO_DIAS * AMARILLO_SIN_OPS_X
        umbral_rojo = INTERVALO_ESPERADO_DIAS * ROJO_SIN_OPS_X
        if dias_sin_ops >= umbral_rojo:
            bandera = "ROJO"
            razones.append(f"sin operaciones en {dias_sin_ops} días (umbral ROJO: {umbral_rojo} días)")
        elif dias_sin_ops >= umbral_amarillo:
            if bandera == "VERDE":
                bandera = "AMARILLO"
            razones.append(f"sin operaciones en {dias_sin_ops} días (umbral AMARILLO: {umbral_amarillo} días)")

    razon_principal = razones[0] if razones else "dentro de todos los límites"

    return {
        "bandera": bandera,
        "pnl_hoy": pnl_hoy,
        "pnl_semana": pnl_semana,
        "dd_actual_usd": dd_actual,
        "dd_pct": dd_pct,
        "ops_semana": ops_semana if not df.empty else 0,
        "dias_sin_ops": dias_sin_ops,
        "razon": razon_principal,
        "razones": razones,
    }


def formato_bloque_robot(nombre, resultado, plan):
    b = resultado
    lineas = [
        f"## {nombre} · {b['bandera']}",
        f"- PnL hoy: {b['pnl_hoy']:+.2f} USD (límite diario: –{plan['limite_diario_usd']:.0f} USD)",
        f"- PnL semana: {b['pnl_semana']:+.2f} USD",
        f"- Drawdown actual: {b['dd_pct']:.1f}% del capital (máx permitido: {LIMITE_DRAWDOWN_PCT*100:.0f}%)",
        f"- Operaciones esta semana: {b['ops_semana']}",
    ]
    if b["dias_sin_ops"] is not None:
        lineas.append(f"- Días sin operaciones: {b['dias_sin_ops']}")
    lineas.append(f"- Razón: {b['razon']}")
    return lineas


def leer_robots_desde_estado():
    if not ROBOTS_ESTADO.exists():
        return {}
    try:
        data = json.loads(ROBOTS_ESTADO.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def main():
    hoy = datetime.now(timezone.utc)
    fecha_str = hoy.strftime("%Y-%m-%d")
    plan = leer_plan()

    ROBOTS_LOGS.mkdir(parents=True, exist_ok=True)
    log_files = list(ROBOTS_LOGS.glob("*.log"))

    robots_estado = leer_robots_desde_estado()

    if not log_files and not robots_estado:
        contenido = [
            f"# Vigía · {fecha_str}",
            "",
            f"Fecha: {ts()}",
            f"Capital de referencia: {plan['capital']:.0f} USD{'  *(supuesto)*' if plan['supuesto'] else ''}",
            "",
            "No se encontraron logs en `robots/logs/` ni `robots/estado.json`.",
            "Cuando los robots tengan operaciones, los logs aparecerán aquí.",
            "",
            "Para crear un log, cada robot debe escribir una línea por operación en:",
            "`robots/logs/<nombre_robot>.log`",
            "Formato: `2026-10-30T06:15:00Z,LONG,65000.00,+1.50`",
        ]
        RESULTADOS.mkdir(parents=True, exist_ok=True)
        ruta_reporte = RESULTADOS / f"vigia_{fecha_str}.md"
        ruta_reporte.write_text("\n".join(contenido) + "\n", encoding="utf-8")
        print("\n".join(contenido))
        return

    bloques = []
    hay_rojo = False

    for log_file in sorted(log_files):
        nombre = log_file.stem
        try:
            df = leer_log_robot(log_file)
            resultado = evaluar_robot(nombre, df, plan, hoy)
            bloque = formato_bloque_robot(nombre, resultado, plan)
            bloques.extend(bloque)
            bloques.append("")

            if resultado["bandera"] == "ROJO":
                hay_rojo = True
                escribir_alerta(nombre, resultado["razon"])
        except Exception as e:
            msg = traceback.format_exc().splitlines()[-1]
            bloques.append(f"## {nombre} · ERROR")
            bloques.append(f"- No se pudo procesar el log: {msg}")
            bloques.append("")
            escribir_alerta(nombre, f"error al procesar log: {msg}")

    if robots_estado and not log_files:
        for nombre, estado in robots_estado.items():
            try:
                equity_val = float(estado.get("equity", 0))
                pnl_hoy = float(estado.get("pnl_hoy", 0))
                capital = plan["capital"]
                dd_usd = float(estado.get("drawdown_usd", 0))
                dd_pct = abs(dd_usd) / capital * 100 if capital > 0 else 0.0

                bandera = "VERDE"
                razon = "estado.json cargado; sin historial de operaciones para análisis completo"
                if pnl_hoy < -plan["limite_diario_usd"]:
                    bandera = "ROJO"
                    razon = f"pérdida diaria {pnl_hoy:.2f} USD supera límite"
                    hay_rojo = True
                    escribir_alerta(nombre, razon)

                bloques.append(f"## {nombre} · {bandera}  *(desde estado.json)*")
                bloques.append(f"- Equity actual: {equity_val:.2f} USD")
                bloques.append(f"- PnL hoy: {pnl_hoy:+.2f} USD")
                bloques.append(f"- Drawdown: {dd_pct:.1f}%")
                bloques.append(f"- Razón: {razon}")
                bloques.append("")
            except Exception as e:
                msg = traceback.format_exc().splitlines()[-1]
                bloques.append(f"## {nombre} · ERROR")
                bloques.append(f"- No se pudo leer estado.json: {msg}")
                bloques.append("")

    supuesto_nota = f"Capital: {plan['capital']:.0f} USD  *(supuesto — no hay MI_PLAN.md)*" if plan["supuesto"] else f"Capital: {plan['capital']:.0f} USD"

    encabezado = [
        f"# Vigía · {fecha_str}",
        "",
        f"Fecha: {ts()}",
        supuesto_nota,
        f"Límite diario: {plan['limite_diario_usd']:.0f} USD · Drawdown máx: {plan['limite_drawdown_usd']:.0f} USD",
        "",
    ]

    contenido = encabezado + bloques

    RESULTADOS.mkdir(parents=True, exist_ok=True)
    ruta_reporte = RESULTADOS / f"vigia_{fecha_str}.md"
    ruta_reporte.write_text("\n".join(contenido) + "\n", encoding="utf-8")

    if hay_rojo:
        print("ALERTA: hay robots en ROJO. Ver resultados/alertas.md")

    print("\n".join(contenido))


if __name__ == "__main__":
    main()
