# Fuentes de datos gratuitas · cómo descargar cada una con Python

Todas guardan el archivo CRUDO en `datos/crudos/<activo>_<temporalidad>_<fuente>.csv`.
Después, siempre, pasa por `curar.py`. Revisadas en octubre de 2026: si una librería cambió y da
error, lee el mensaje, revisa su documentación y corrige; no inventes funciones.

| Fuente | Mercados | Registro | Volumen | Límites que debes decir |
| --- | --- | --- | --- | --- |
| Yahoo Finance (`yfinance`) | acciones, ETF, índices, cripto, algunas divisas | no | sí (acciones y cripto) | 1 h: últimos ~730 días · 15 min o menos: últimos ~60 días · 1 min: ~30 días |
| Alpaca (`alpaca-py`) | acciones de EE. UU. y cripto | cripto no · acciones sí (claves gratis) | sí | acciones: con el plan gratis puede pedir `feed=DataFeed.IEX` |
| Dukascopy (`dukascopy-python`) | forex, metales, índices CFD, algunas cripto | no | de ticks (actividad del bróker, no volumen real del mercado) | precios bid o ask, elige uno y dilo |
| HistData (`histdata`) | forex, algunos índices y petróleo | no | no (siempre 0) | solo 1 minuto · hora de Nueva York SIN cambio de verano (`--zona EST`) · un archivo por mes |

Instalar lo que se use: `pip install yfinance alpaca-py dukascopy-python histdata pandas`

## Yahoo Finance
```python
import yfinance as yf
df = yf.download("BTC-USD", period="5y", interval="1d", auto_adjust=True, multi_level_index=False)
df.reset_index().to_csv("datos/crudos/btc-usd_1d_yahoo.csv", index=False)
```
- Símbolos de Yahoo: `AAPL`, `SPY`, `^GSPC` (índice), `BTC-USD`, `EURUSD=X`, `GC=F` (futuro de oro).
- `auto_adjust=True` = precios ajustados por splits y dividendos. Decláralo en el informe.
- `period` o `start`/`end`. Para 1 h usa como mucho `period="730d"`.
- Zona: las fechas diarias vienen sin hora; las intradía, con zona del mercado. `--zona America/New_York` para acciones de EE. UU.

## Alpaca
Cripto (sin claves):
```python
from datetime import datetime
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
c = CryptoHistoricalDataClient()
r = CryptoBarsRequest(symbol_or_symbols="BTC/USD", timeframe=TimeFrame.Hour, start=datetime(2021, 1, 1))
c.get_crypto_bars(r).df.reset_index().to_csv("datos/crudos/btc-usd_1h_alpaca.csv", index=False)
```
Acciones (con claves): el trader crea sus claves gratis en alpaca.markets y las escribe ÉL en el
archivo `.env` de la cueva (que nunca se sube a GitHub):
```
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
```
Tú NUNCA le pides las claves, no las escribes en el chat ni en ningún archivo, y no las imprimes.
```python
import os
from datetime import datetime
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import Adjustment, DataFeed
env = dict(l.strip().split("=", 1) for l in open(".env") if "=" in l and not l.startswith("#"))
c = StockHistoricalDataClient(env["ALPACA_API_KEY"], env["ALPACA_SECRET_KEY"])
r = StockBarsRequest(symbol_or_symbols="QQQ", timeframe=TimeFrame.Hour, start=datetime(2020, 1, 1),
                     adjustment=Adjustment.ALL, feed=DataFeed.IEX)
c.get_stock_bars(r).df.reset_index().to_csv("datos/crudos/qqq_1h_alpaca.csv", index=False)
```
- Las fechas de Alpaca vienen en UTC. Si no existe `.env` o falta una clave, PARA y explica cómo crearla.

## Dukascopy
```python
from datetime import datetime
import dukascopy_python as d
from dukascopy_python.instruments import INSTRUMENT_FX_MAJORS_EUR_USD
df = d.fetch(INSTRUMENT_FX_MAJORS_EUR_USD, d.INTERVAL_HOUR_1, d.OFFER_SIDE_BID,
             datetime(2019, 1, 1), datetime(2026, 1, 1))
df.reset_index().to_csv("datos/crudos/eurusd_1h_dukascopy.csv", index=False)
```
- Intervalos: `INTERVAL_MIN_1`, `_MIN_5`, `_MIN_15`, `_MIN_30`, `INTERVAL_HOUR_1`, `_HOUR_4`, `INTERVAL_DAY_1`.
- Los instrumentos están en `dukascopy_python.instruments` (por ejemplo `INSTRUMENT_FX_METALS_XAU_USD`,
  `INSTRUMENT_IDX_AMERICA_E_NQ_100`). Búscalo con `dir()` si no lo conoces.
- Las fechas vienen en UTC. Rangos largos en 1 minuto tardan: descarga por años.

## HistData
```python
from histdata import download_hist_data
# años ya cerrados: el año completo, con month=None
download_hist_data(year="2024", month=None, pair="eurusd", time_frame="M1", platform="ASCII",
                   output_directory="datos/crudos")
# año en curso: mes a mes
download_hist_data(year="2026", month="9", pair="eurusd", time_frame="M1", platform="ASCII",
                   output_directory="datos/crudos")
```
- Años cerrados: SOLO con `month=None` (pedirlos por mes da error). Año en curso: SOLO por mes.
- Cada descarga es un .zip: descomprímelo y une los CSV en uno solo antes de curar. Vienen sin encabezado, con `;` y fecha `AAAAMMDD HHMMSS`:
  `curar.py` los reconoce.
- Siempre `--zona EST` al curar (hora de Nueva York sin cambio de verano).
- Para otras temporalidades, primero cura en 1 minuto y después agrupa (resample) a la que necesites.
