import urllib.request
import json
import csv
import time
import datetime
import threading
import os

SYMBOLS    = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BCHUSDT"]
INTERVALS  = ["4h", "1h", "15m"]
YEARS_BACK = 3
LIMIT      = 1000
BASE_URL   = "https://api.binance.com/api/v3/klines"
LOCK       = threading.Lock()

def ts_to_str(ms):
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.UTC).strftime("%Y-%m-%d %H:%M")

def fetch(symbol, interval):
    end_ms   = int(time.time() * 1000)
    start_ms = end_ms - (YEARS_BACK * 365 * 24 * 60 * 60 * 1000)
    rows     = []
    current  = start_ms

    while current < end_ms:
        url = f"{BASE_URL}?symbol={symbol}&interval={interval}&startTime={current}&limit={LIMIT}"
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                data = json.loads(resp.read())
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
        time.sleep(0.15)

    filename = f"{symbol}_{interval}.csv"
    with open(filename, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "open", "high", "low", "close", "volume"])
        w.writerows(rows)

    with LOCK:
        first = rows[0][0] if rows else "?"
        last  = rows[-1][0] if rows else "?"
        print(f"  OK  {filename:<22} {len(rows):>6} velas   {first} → {last}")

tasks = [(s, i) for s in SYMBOLS for i in INTERVALS]

# Skip BTCUSDT 4h — ya existe
tasks = [(s, i) for s, i in tasks if not (s == "BTCUSDT" and i == "4h")]

print(f"Descargando {len(tasks)} archivos en paralelo (hilos de 5)...\n")

threads = []
sem = threading.Semaphore(5)

def run(symbol, interval):
    with sem:
        fetch(symbol, interval)

for s, i in tasks:
    t = threading.Thread(target=run, args=(s, i))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print(f"\nTodo listo. Archivos en: {os.getcwd()}")
