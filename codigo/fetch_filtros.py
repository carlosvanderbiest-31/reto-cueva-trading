# Baja datos gratis para los filtros H2, H4, H6, H7 y los deja en datos/
import urllib.request, json, ssl, time
import pandas as pd
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36'}

def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40, context=ctx).read()

# --- H2a: Fear & Greed (alternative.me) ---
d=json.loads(get('https://api.alternative.me/fng/?limit=0&format=json'))['data']
fng=pd.DataFrame([{'fecha':pd.to_datetime(int(x['timestamp']),unit='s'),'fng':int(x['value'])} for x in d])
fng=fng.sort_values('fecha'); fng.to_csv('datos/btc_fng.csv',index=False)
print('FNG   :', len(fng), fng['fecha'].min().date(), '->', fng['fecha'].max().date())

# --- H2b: MVRV Z-score (bitcoin-data.com) ---
d=json.loads(get('https://bitcoin-data.com/v1/mvrv-zscore'))
mv=pd.DataFrame([{'fecha':pd.to_datetime(x['d']),'mvrvz':float(x['mvrvZscore'])} for x in d])
mv=mv.sort_values('fecha'); mv.to_csv('datos/btc_mvrvz.csv',index=False)
print('MVRVz :', len(mv), mv['fecha'].min().date(), '->', mv['fecha'].max().date())

# --- H4: flujo ETF (bitcoin-data.com) ---
d=json.loads(get('https://bitcoin-data.com/v1/etf-flow-btc'))
etf=pd.DataFrame([{'fecha':pd.to_datetime(x['d']),'flujo':float(x['etfFlow'])} for x in d])
etf=etf.sort_values('fecha'); etf.to_csv('datos/btc_etfflow.csv',index=False)
print('ETF   :', len(etf), etf['fecha'].min().date(), '->', etf['fecha'].max().date())

# --- H6: funding (Binance perp, paginado) ---
rows=[]; start=1567296000000  # 2019-09-01
while True:
    d=json.loads(get(f'https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime={start}&limit=1000'))
    if not d: break
    rows+=d
    nxt=d[-1]['fundingTime']+1
    if nxt<=start or len(d)<1000: start=nxt;
    start=nxt
    if len(d)<1000: break
    time.sleep(0.2)
fund=pd.DataFrame([{'fecha':pd.to_datetime(x['fundingTime'],unit='ms'),'funding':float(x['fundingRate'])} for x in rows])
fund=fund.drop_duplicates('fecha').sort_values('fecha'); fund.to_csv('datos/btc_funding.csv',index=False)
print('FUND  :', len(fund), fund['fecha'].min().date(), '->', fund['fecha'].max().date())

# --- H7: Coinbase Premium = (coinbase - binance)/binance, diario ---
# Coinbase daily candles (granularity 86400, 300 max por llamada)
import datetime as dt
cb=[]; end=dt.datetime(2026,11,1)
while end>dt.datetime(2017,8,1):
    s=end-dt.timedelta(days=300)
    u=f'https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400&start={s.isoformat()}&end={end.isoformat()}'
    try:
        d=json.loads(get(u))  # [time, low, high, open, close, volume]
        cb+=[{'fecha':pd.to_datetime(c[0],unit='s'),'cb_close':c[4]} for c in d]
    except Exception as e:
        print('  cb err', repr(e)[:60])
    end=s; time.sleep(0.25)
cbd=pd.DataFrame(cb).drop_duplicates('fecha').sort_values('fecha')
# binance daily close desde el 4h que ya tenemos
b=pd.read_csv('datos/BTCUSDT_4h.csv',parse_dates=['time'])
b['fecha']=b['time'].dt.tz_localize(None).dt.floor('D')
bd=b.groupby('fecha')['close'].last().reset_index().rename(columns={'close':'bi_close'})
prem=cbd.merge(bd,on='fecha',how='inner')
prem['premium']=(prem['cb_close']-prem['bi_close'])/prem['bi_close']
prem[['fecha','premium']].to_csv('datos/btc_premium.csv',index=False)
print('PREM  :', len(prem), prem['fecha'].min().date(), '->', prem['fecha'].max().date())
print('\nTodo guardado en datos/')
