"""
Descarga el histórico COMPLETO disponible en Binance para cada símbolo.
Inicio estimado en Binance:
  BTC/ETH/XRP/BCH: sep 2017
  SOL: ago 2020
No hay límite de años — descarga hasta la primera vela disponible.
"""

import urllib.request
import json
import csv
import time
import datetime
import os

SYMBOLS   = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BCHUSDT"]
INTERVALS = ["4h", "1h", "15m"]
LIMIT     = 1000

ENDPOINTS = [
    "https://data-api.binance.vision/api/v3/klines",
    "https://api1.binance.com/api/v3/klines",
    "https://api2.binance.com/api/v3/klines",
    "https://api3.binance.com/api/v3/klines",
]

# Inicio más antiguo posible (Binance abrió sep 2017)
ORIGIN_MS = int(datetime.datetime(2017, 1, 1, tzinfo=datetime.timezone.utc).timestamp() * 1000)

def ts(ms):
    return datetime.datetime.fromtimestamp(
        ms / 1000, datetime.timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S+00:00")

def find_endpoint(symbol, interval):
    for ep in ENDPOINTS:
        try:
            url = f"{ep}?symbol={symbol}&interval={interval}&limit=1"
            with urllib.request.urlopen(url, timeout=10) as r:
                json.loads(r.read())
            return ep
        except Exception:
            continue
    return None

def fetch_full(symbol, interval):
    print(f"  {symbol} {interval} ...", end=" ", flush=True)

    ep = find_endpoint(symbol, interval)
    if not ep:
        print("SIN ENDPOINT")
        return

    end_ms  = int(time.time() * 1000)
    current = ORIGIN_MS
    rows    = []
    batch   = 0

    while current < end_ms:
        url = (f"{ep}?symbol={symbol}&interval={interval}"
               f"&startTime={current}&limit={LIMIT}")
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.loads(r.read())
        except Exception as e:
            print(f"\n    Error en batch {batch}: {e} — reintentando...")
            time.sleep(3)
            continue

        if not data:
            break

        for k in data:
            rows.append([ts(k[0]), k[1], k[2], k[3], k[4], k[5]])

        last = data[-1][0]
        batch += 1
        if batch % 50 == 0:
            print(f"\n    {len(rows):>7} velas hasta {ts(last)[:10]} ...", end=" ", flush=True)

        if last >= end_ms or len(data) < LIMIT:
            break
        current = last + 1
        time.sleep(0.25)

    if not rows:
        print("SIN DATOS")
        return

    fname = f"{symbol}_{interval}.csv"
    with open(fname, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time", "open", "high", "low", "close", "volume"])
        w.writerows(rows)

    print(f"\n    OK  {len(rows):>7} velas   {rows[0][0][:10]} / {rows[-1][0][:10]}")

# ── ejecutar secuencial (evita throttling) ────────────────────────────────────
print(f"Descargando histórico COMPLETO — {len(SYMBOLS)} símbolos × {len(INTERVALS)} timeframes\n")

for symbol in SYMBOLS:
    for interval in INTERVALS:
        fetch_full(symbol, interval)
        time.sleep(0.5)

print("\nVerificación final:")
for s in SYMBOLS:
    for i in INTERVALS:
        f = f"{s}_{i}.csv"
        if os.path.exists(f):
            with open(f, encoding="utf-8") as fh:
                n = sum(1 for _ in fh) - 1
            print(f"  {f:<25} {n:>8} velas")
        else:
            print(f"  {f:<25} FALTA")
print("\nListo.")
