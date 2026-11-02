"""
datos_refresh.py · Cueva TIS
Actualiza diariamente los CSVs de activos activos con las velas nuevas.
Cron: 0 6 * * * /usr/bin/python3 /root/cueva/automatizacion/datos_refresh.py
"""
import os
import sys
import subprocess
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATOS = BASE / "datos"
RESULTADOS = BASE / "resultados"
CURAR = BASE / ".claude" / "skills" / "datos" / "curar.py"
ESTADO_CUEVA = RESULTADOS / "estado_cueva.md"
REFRESH_LOG = RESULTADOS / "refresh_log.md"
ALERTAS = RESULTADOS / "alertas.md"

ACTIVOS_DEFAULT = [
    {
        "ticker_yahoo": "BTC-USD",
        "csv_destino": "btcusdt_1d_yahoo.csv",
        "crudo": "btcusd_1d_yahoo_crudo.csv",
        "temporalidad": "1d",
        "mercado": "cripto",
        "zona": "UTC",
        "informe": "btcusd_1d_yahoo_calidad.md",
    },
    {
        "ticker_yahoo": "ETH-USD",
        "csv_destino": "ethusdt_1d_yahoo.csv",
        "crudo": "ethusdt_1d_yahoo_crudo.csv",
        "temporalidad": "1d",
        "mercado": "cripto",
        "zona": "UTC",
        "informe": "ethusdt_1d_yahoo_calidad.md",
    },
    {
        "ticker_yahoo": "SOL-USD",
        "csv_destino": "solusdt_1d_yahoo.csv",
        "crudo": "solusdt_1d_yahoo_crudo.csv",
        "temporalidad": "1d",
        "mercado": "cripto",
        "zona": "UTC",
        "informe": "solusdt_1d_yahoo_calidad.md",
    },
    {
        "ticker_yahoo": "XRP-USD",
        "csv_destino": "xrpusdt_1d_yahoo.csv",
        "crudo": "xrpusdt_1d_yahoo_crudo.csv",
        "temporalidad": "1d",
        "mercado": "cripto",
        "zona": "UTC",
        "informe": "xrpusdt_1d_yahoo_calidad.md",
    },
    {
        "ticker_yahoo": "BCH-USD",
        "csv_destino": "bchusdt_1d_yahoo.csv",
        "crudo": "bchusdt_1d_yahoo_crudo.csv",
        "temporalidad": "1d",
        "mercado": "cripto",
        "zona": "UTC",
        "informe": "bchusdt_1d_yahoo_calidad.md",
    },
]

ACTIVO_BTC_1H = {
    "csv_destino": "btcusd_1h_alpaca.csv",
    "crudo": "btcusd_1h_alpaca_crudo.csv",
    "temporalidad": "1h",
    "mercado": "cripto",
    "zona": "UTC",
    "informe": "btcusd_1h_alpaca_calidad.md",
    "symbol": "BTC/USD",
}


def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def escribir_alerta(activo, mensaje):
    ALERTAS.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTAS, "a", encoding="utf-8") as f:
        f.write(f"- {ts()} · {activo} · {mensaje}\n")


def ultima_fecha_csv(ruta_csv):
    if not ruta_csv.exists():
        return None
    try:
        df = pd.read_csv(ruta_csv, usecols=[0])
        if df.empty:
            return None
        col = df.columns[0]
        fechas = pd.to_datetime(df[col], errors="coerce").dropna()
        if fechas.empty:
            return None
        return fechas.max().to_pydatetime().replace(tzinfo=timezone.utc)
    except Exception:
        return None


def descargar_yahoo(ticker, desde, hasta):
    import yfinance as yf
    inicio = (desde + timedelta(days=1)).strftime("%Y-%m-%d") if desde else "2019-01-01"
    fin = hasta.strftime("%Y-%m-%d")
    df = yf.download(
        ticker,
        start=inicio,
        end=fin,
        interval="1d",
        auto_adjust=True,
        multi_level_index=False,
        progress=False,
    )
    if df.empty:
        return None
    df = df.reset_index()
    return df


def descargar_alpaca_1h(symbol, desde):
    from alpaca.data.historical import CryptoHistoricalDataClient
    from alpaca.data.requests import CryptoBarsRequest
    from alpaca.data.timeframe import TimeFrame

    inicio = desde + timedelta(hours=1) if desde else datetime(2021, 1, 1, tzinfo=timezone.utc)
    fin = datetime.now(timezone.utc) - timedelta(hours=1)
    client = CryptoHistoricalDataClient()
    req = CryptoBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Hour,
        start=inicio,
        end=fin,
    )
    bars = client.get_crypto_bars(req)
    df = bars.df.reset_index()
    return df if not df.empty else None


def normalizar_yahoo(df):
    df = df.copy()
    col_fecha = [c for c in df.columns if str(c).lower() in ("date", "datetime", "fecha", "timestamp")]
    if col_fecha:
        df = df.rename(columns={col_fecha[0]: "fecha"})
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce", utc=True)
    for col in ("Open", "High", "Low", "Close", "Volume"):
        col_lower = col.lower()
        if col in df.columns:
            df = df.rename(columns={col: col_lower})
    for c in ("open", "high", "low", "close", "volume"):
        if c not in df.columns:
            df[c] = 0.0
    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return df[["fecha", "open", "high", "low", "close", "volume"]]


def normalizar_alpaca(df):
    df = df.copy()
    col_map = {}
    for c in df.columns:
        cl = str(c).lower()
        if cl in ("timestamp", "fecha", "date", "datetime"):
            col_map[c] = "fecha"
        elif cl == "open":
            col_map[c] = "open"
        elif cl == "high":
            col_map[c] = "high"
        elif cl == "low":
            col_map[c] = "low"
        elif cl == "close":
            col_map[c] = "close"
        elif cl in ("volume", "trade_count", "vwap"):
            if "volume" not in col_map.values():
                col_map[c] = "volume"
    df = df.rename(columns=col_map)
    if "fecha" not in df.columns:
        if df.index.name and str(df.index.name).lower() in ("timestamp", "fecha"):
            df = df.reset_index().rename(columns={df.index.name: "fecha"})
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce", utc=True)
    for c in ("open", "high", "low", "close", "volume"):
        if c not in df.columns:
            df[c] = 0.0
    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return df[["fecha", "open", "high", "low", "close", "volume"]]


def append_sin_duplicados(csv_existente, df_nuevo):
    if csv_existente.exists():
        df_viejo = pd.read_csv(csv_existente)
        df_combinado = pd.concat([df_viejo, df_nuevo], ignore_index=True)
    else:
        df_combinado = df_nuevo.copy()
    df_combinado["fecha"] = pd.to_datetime(df_combinado["fecha"], errors="coerce")
    df_combinado = df_combinado.dropna(subset=["fecha"])
    df_combinado = df_combinado.drop_duplicates(subset=["fecha"], keep="last")
    df_combinado = df_combinado.sort_values("fecha")
    df_combinado["fecha"] = df_combinado["fecha"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df_combinado.to_csv(csv_existente, index=False)
    return len(df_nuevo)


def correr_curar(crudo, mercado, temporalidad, zona, salida, informe):
    if not CURAR.exists():
        return False, f"curar.py no encontrado en {CURAR}"
    cmd = [
        sys.executable,
        str(CURAR),
        str(crudo),
        "--mercado", mercado,
        "--temporalidad", temporalidad,
        "--zona", zona,
        "--salida", str(salida),
        "--informe", str(informe),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr.strip() or result.stdout.strip()
    return True, None


def leer_activos_estado_cueva():
    if not ESTADO_CUEVA.exists():
        return None
    try:
        texto = ESTADO_CUEVA.read_text(encoding="utf-8")
        lineas = [l.strip() for l in texto.splitlines() if "|" in l]
        if len(lineas) < 2:
            return None
        encabezado = [c.strip().lower() for c in lineas[0].split("|") if c.strip()]
        activos = []
        for linea in lineas[2:]:
            celdas = [c.strip() for c in linea.split("|") if c.strip() != ""]
            if len(celdas) < len(encabezado):
                continue
            fila = dict(zip(encabezado, celdas))
            if fila.get("activo", "").lower() in ("si", "sí", "true", "yes", "1"):
                activos.append(fila)
        return activos if activos else None
    except Exception:
        return None


def procesar_activo_yahoo(activo, hoy, resumen):
    nombre = activo["ticker_yahoo"]
    csv_destino = DATOS / activo["csv_destino"]
    crudo = DATOS / "crudos" / activo["crudo"]
    crudo.parent.mkdir(parents=True, exist_ok=True)

    ultima = ultima_fecha_csv(csv_destino)
    try:
        df_nuevo = descargar_yahoo(nombre, ultima, hoy)
    except Exception as e:
        msg = f"Error descargando {nombre}: {e}"
        escribir_alerta(nombre, msg)
        resumen.append(f"- {nombre}: ERROR · {msg}")
        return

    if df_nuevo is None or df_nuevo.empty:
        resumen.append(f"- {nombre}: sin velas nuevas")
        return

    df_norm = normalizar_yahoo(df_nuevo)
    df_norm.to_csv(crudo, index=False)

    velas_nuevas = append_sin_duplicados(csv_destino, df_norm)

    ok, err = correr_curar(
        crudo=crudo,
        mercado=activo["mercado"],
        temporalidad=activo["temporalidad"],
        zona=activo["zona"],
        salida=csv_destino,
        informe=RESULTADOS / activo["informe"],
    )
    if not ok:
        escribir_alerta(nombre, f"curar.py falló: {err}")
        resumen.append(f"- {nombre}: {velas_nuevas} velas nuevas · AVISO curar.py: {err}")
    else:
        resumen.append(f"- {nombre}: {velas_nuevas} velas nuevas · curar.py OK")


def procesar_activo_alpaca_1h(resumen):
    activo = ACTIVO_BTC_1H
    nombre = "BTC/USD 1h (Alpaca)"
    csv_destino = DATOS / activo["csv_destino"]
    crudo = DATOS / "crudos" / activo["crudo"]
    crudo.parent.mkdir(parents=True, exist_ok=True)

    ultima = ultima_fecha_csv(csv_destino)
    try:
        df_nuevo = descargar_alpaca_1h(activo["symbol"], ultima)
    except ImportError:
        resumen.append(f"- {nombre}: alpaca-py no instalado, saltado")
        return
    except Exception as e:
        msg = f"Error descargando Alpaca 1h: {e}"
        escribir_alerta(nombre, msg)
        resumen.append(f"- {nombre}: ERROR · {msg}")
        return

    if df_nuevo is None or df_nuevo.empty:
        resumen.append(f"- {nombre}: sin velas nuevas")
        return

    df_norm = normalizar_alpaca(df_nuevo)
    df_norm.to_csv(crudo, index=False)

    velas_nuevas = append_sin_duplicados(csv_destino, df_norm)

    ok, err = correr_curar(
        crudo=crudo,
        mercado=activo["mercado"],
        temporalidad=activo["temporalidad"],
        zona=activo["zona"],
        salida=csv_destino,
        informe=RESULTADOS / activo["informe"],
    )
    if not ok:
        escribir_alerta(nombre, f"curar.py falló: {err}")
        resumen.append(f"- {nombre}: {velas_nuevas} velas nuevas · AVISO curar.py: {err}")
    else:
        resumen.append(f"- {nombre}: {velas_nuevas} velas nuevas · curar.py OK")


def main():
    hoy = datetime.now(timezone.utc)
    resumen = []

    activos_estado = leer_activos_estado_cueva()
    if activos_estado:
        activos = activos_estado
    else:
        activos = ACTIVOS_DEFAULT

    for activo in activos:
        try:
            procesar_activo_yahoo(activo, hoy, resumen)
        except Exception as e:
            nombre = activo.get("ticker_yahoo", "desconocido")
            msg = traceback.format_exc().splitlines()[-1]
            escribir_alerta(nombre, f"excepción inesperada: {msg}")
            resumen.append(f"- {nombre}: ERROR inesperado · {msg}")

    try:
        procesar_activo_alpaca_1h(resumen)
    except Exception as e:
        msg = traceback.format_exc().splitlines()[-1]
        escribir_alerta("BTC/USD 1h Alpaca", f"excepción inesperada: {msg}")
        resumen.append(f"- BTC/USD 1h Alpaca: ERROR inesperado · {msg}")

    RESULTADOS.mkdir(parents=True, exist_ok=True)
    log_lineas = [
        f"# Refresh log · {hoy.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"Fecha: {ts()}",
        f"Activos procesados: {len(activos) + 1}",
        "",
        "## Resultado por activo",
    ] + resumen + [""]

    modo = "a" if REFRESH_LOG.exists() else "w"
    with open(REFRESH_LOG, modo, encoding="utf-8") as f:
        f.write("\n".join(log_lineas) + "\n---\n\n")

    print("\n".join(log_lineas))


if __name__ == "__main__":
    main()
