import urllib.request
import json
import csv
import time
import datetime
import threading
import os

SYMBOLS    = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BCHUSDT"]
INTERVALS  = ["4h", "1h", "15m"]
YEARS_BACK = 4
LIMIT      = 1000
LOCK       = threading.Lock()

# Endpoints alternativos de Binance (prueba en orden)
ENDPOINTS = [
    "https://data-api.binance.vision/api/v3/klines",
    "https://api1.binance.com/api/v3/klines",
    "https://api2.binance.com/api/v3/klines",
    "https://api3.binance.com/api/v3/klines",
]

def ts_to_str(ms):
    dt = datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S+00:00")

def fetch_url(url, timeout=20):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read())

def fetch(symbol, interval):
    # Encontrar endpoint que funcione
    base_url = None
    for ep in ENDPOINTS:
        try:
            test_url = f"{ep}?symbol={symbol}&interval={interval}&limit=1"
            fetch_url(test_url, timeout=10)
            base_url = ep
            break
        except Exception:
            continue

    if not base_url:
        with LOCK:
            print(f"  [SKIP] {symbol} {interval}: ningun endpoint disponible")
        return

    end_ms   = int(time.time() * 1000)
    start_ms = end_ms - (YEARS_BACK * 365 * 24 * 60 * 60 * 1000)
    rows     = []
    current  = start_ms

    while current < end_ms:
        url = f"{base_url}?symbol={symbol}&interval={interval}&startTime={current}&limit={LIMIT}"
        try:
            data = fetch_url(url)
        except Exception as e:
            with LOCK:
                print(f"  [ERROR] {symbol} {interval}: {e}")
            break

        if not data:
            break

        for k in data:
            rows.append([ts_to_str(k[0]), k[1], k[2], k[3], k[4], k[5]])

        last_ts = data[-1][0]
        if last_ts >= end_ms or len(data) < LIMIT:
            break
        current = last_ts + 1
        time.sleep(0.2)

    if not rows:
        with LOCK:
            print(f"  [VACIO] {symbol} {interval}")
        return

    filename = f"{symbol}_{interval}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time", "open", "high", "low", "close", "volume"])
        w.writerows(rows)

    with LOCK:
        print(f"  OK  {filename:<25} {len(rows):>7} velas   {rows[0][0][:10]} / {rows[-1][0][:10]}")

tasks = [(s, i) for s in SYMBOLS for i in INTERVALS]
print(f"Descargando {len(tasks)} archivos — 4 anos, timestamps UTC...\n")

sem     = threading.Semaphore(3)   # menos paralelas para no saturar
threads = []

def run(s, i):
    with sem:
        fetch(s, i)

for s, i in tasks:
    t = threading.Thread(target=run, args=(s, i))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# Verificar resultado
print("\nVerificacion final:")
for s in SYMBOLS:
    for i in INTERVALS:
        f = f"{s}_{i}.csv"
        if os.path.exists(f):
            with open(f, encoding="utf-8") as fh:
                n = sum(1 for _ in fh) - 1
            print(f"  {f:<25} {n:>7} velas")
        else:
            print(f"  {f:<25} FALTA")
