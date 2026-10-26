import urllib.request
import json
import csv
import time
import datetime

SYMBOL   = "BTCUSDT"
INTERVAL = "4h"
LIMIT    = 1000
OUTPUT   = "BTCUSDT_4h.csv"

# 3 years back from today
end_ms   = int(time.time() * 1000)
start_ms = end_ms - (3 * 365 * 24 * 60 * 60 * 1000)

BASE_URL = "https://api.binance.com/api/v3/klines"

rows = []
current = start_ms

print(f"Descargando {SYMBOL} {INTERVAL} desde {datetime.datetime.utcfromtimestamp(start_ms/1000).date()} ...")

while current < end_ms:
    url = f"{BASE_URL}?symbol={SYMBOL}&interval={INTERVAL}&startTime={current}&limit={LIMIT}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"Error: {e}")
        break

    if not data:
        break

    for k in data:
        rows.append({
            "time":   datetime.datetime.utcfromtimestamp(k[0]/1000).strftime("%Y-%m-%d %H:%M"),
            "open":   k[1],
            "high":   k[2],
            "low":    k[3],
            "close":  k[4],
            "volume": k[5],
        })

    last_ts = data[-1][0]
    print(f"  ...hasta {datetime.datetime.utcfromtimestamp(last_ts/1000).date()} ({len(rows)} velas)")
    if last_ts >= end_ms or len(data) < LIMIT:
        break
    current = last_ts + 1
    time.sleep(0.2)

with open(OUTPUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["time","open","high","low","close","volume"])
    writer.writeheader()
    writer.writerows(rows)

print(f"\nListo. {len(rows)} velas guardadas en {OUTPUT}")
print(f"  Primera: {rows[0]['time']}")
print(f"  Última:  {rows[-1]['time']}")
