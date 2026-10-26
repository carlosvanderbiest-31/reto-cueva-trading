"""Curación de datos de precios · skill datos (cueva TIS).

Lee un CSV crudo de cualquier fuente, lo deja en un formato único y revisa su calidad.
No inventa precios: elimina lo imposible, marca lo dudoso y reporta los huecos.

Uso:
  python .claude/skills/datos/curar.py datos/crudos/btc-usd_1h_yahoo.csv \
      --mercado cripto --temporalidad 1h --zona UTC \
      --salida datos/btc-usd_1h_yahoo.csv \
      --informe resultados/btc-usd_1h_yahoo_calidad.md

--mercado: cripto (24/7) · forex (domingo 17:00 a viernes 17:00 de Nueva York) · bolsa (lunes a viernes)
--zona: zona horaria de las fechas del CSV crudo si vienen sin zona (UTC, America/New_York, EST...).
Salida: fecha (UTC, ISO), open, high, low, close, volume. Volumen vacío si la fuente no lo trae.
"""
import argparse, sys
import numpy as np
import pandas as pd

ALIAS = {
    'fecha': ['fecha', 'date', 'datetime', 'time', 'timestamp', 'gmt time', 'local time', 'data'],
    'open': ['open', 'apertura', 'abertura', 'o'],
    'high': ['high', 'maximo', 'máximo', 'max', 'h'],
    'low': ['low', 'minimo', 'mínimo', 'min', 'l'],
    'close': ['close', 'cierre', 'fechamento', 'c', 'adj close'],
    'volume': ['volume', 'volumen', 'vol', 'v', 'tick volume', 'tickvol'],
}
PASO = {'1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min', '1h': '1h', '4h': '4h', '1d': '1D'}
MIN_ANIOS_APTA, MIN_ANIOS = 3.0, 1.0      # provisional: menos de 1 año = NO APTA; de 1 a 3 = aviso
MAX_ELIMINADAS, MAX_HUECOS = 0.05, 0.05    # provisional: más del 5 % = NO APTA


def leer(ruta):
    df = pd.read_csv(ruta, sep=None, engine='python')
    if len(df.columns) in (5, 6) and not any(str(c).strip().lower() in ALIAS['fecha'] for c in df.columns):
        df = pd.read_csv(ruta, sep=None, engine='python', header=None)   # sin encabezado (HistData)
        df.columns = ['fecha', 'open', 'high', 'low', 'close', 'volume'][:len(df.columns)]
    cols = {}
    for c in df.columns:
        n = str(c).strip().lower()
        for k, alias in ALIAS.items():
            if n in alias and k not in cols.values():
                cols[c] = k
                break
    df = df.rename(columns=cols)
    falta = [k for k in ('fecha', 'open', 'high', 'low', 'close') if k not in df.columns]
    if falta:
        sys.exit(f'No encuentro las columnas {falta}. Columnas del archivo: {list(df.columns)}')
    if 'volume' not in df.columns:
        df['volume'] = np.nan
    return df[['fecha', 'open', 'high', 'low', 'close', 'volume']]


def a_utc(serie, zona):
    t = serie.astype(str).str.strip()
    if t.str.fullmatch(r'\d{8} \d{6}').all():
        f = pd.to_datetime(t, format='%Y%m%d %H%M%S', errors='coerce')
    elif t.str.fullmatch(r'\d{10,13}').all():
        f = pd.to_datetime(t.astype('int64'), unit='ms' if t.str.len().max() > 10 else 's', utc=True)
    else:
        f = pd.to_datetime(t, errors='coerce', format='mixed')
    if getattr(f.dt, 'tz', None) is None:
        if zona.upper() == 'EST':   # hora de Nueva York sin cambio de verano (HistData)
            f = f + pd.Timedelta(hours=5)
            return f.dt.tz_localize('UTC')
        return f.dt.tz_localize(zona, ambiguous='NaT', nonexistent='NaT').dt.tz_convert('UTC')
    return f.dt.tz_convert('UTC')


def esperadas(ini, fin, paso, mercado):
    idx = pd.date_range(ini, fin, freq=paso, tz='UTC')
    if mercado == 'cripto':
        return idx
    if mercado == 'forex':
        ny = idx.tz_convert('America/New_York')
        dia, hora = ny.dayofweek, ny.hour
        abierto = ~((dia == 5) | ((dia == 4) & (hora >= 17)) | ((dia == 6) & (hora < 17)))
        return idx[abierto]
    ny = idx.tz_convert('America/New_York')
    return idx[ny.dayofweek < 5]


def main():
    a = argparse.ArgumentParser()
    a.add_argument('crudo')
    a.add_argument('--mercado', required=True, choices=['cripto', 'forex', 'bolsa'])
    a.add_argument('--temporalidad', required=True, choices=list(PASO))
    a.add_argument('--zona', default='UTC')
    a.add_argument('--salida', required=True)
    a.add_argument('--informe', required=True)
    o = a.parse_args()

    df = leer(o.crudo)
    n0 = len(df)
    df['fecha'] = a_utc(df['fecha'], o.zona)
    for c in ('open', 'high', 'low', 'close', 'volume'):
        df[c] = pd.to_numeric(df[c], errors='coerce')

    sin_fecha = int(df['fecha'].isna().sum())
    df = df.dropna(subset=['fecha']).sort_values('fecha')

    dup_iguales = int(df.duplicated().sum())
    df = df.drop_duplicates()
    dup_distintas = int(df.duplicated('fecha').sum())
    df = df.drop_duplicates('fecha', keep='first')

    p = df[['open', 'high', 'low', 'close']]
    imposibles = (p.isna().any(axis=1) | (p <= 0).any(axis=1)
                  | (df['high'] < p[['open', 'close']].max(axis=1))
                  | (df['low'] > p[['open', 'close']].min(axis=1)))
    n_imp = int(imposibles.sum())
    df = df[~imposibles]

    # saltos raros: retorno muy lejos de lo normal (8 veces la desviación robusta). Se marcan, no se borran.
    r = np.log(df['close']).diff()
    mad = (r - r.median()).abs().median() * 1.4826
    saltos = df.loc[(r - r.median()).abs() > 8 * mad, 'fecha'] if mad > 0 else df['fecha'].iloc[:0]

    paso = PASO[o.temporalidad]
    if o.temporalidad == '1d':
        dias = df['fecha'].dt.tz_convert('America/New_York').dt.normalize() if o.mercado != 'cripto' else df['fecha'].dt.normalize()
        tiene = pd.DatetimeIndex(dias.dt.tz_localize(None).unique())
        exp = pd.date_range(tiene.min(), tiene.max(), freq='D')
        exp = exp if o.mercado == 'cripto' else exp[exp.dayofweek < 5]
        faltan = exp.difference(tiene)
    elif o.mercado == 'bolsa':
        # intradía de bolsa: huecos solo dentro de cada día con datos (no se conocen festivos ni sesiones)
        faltan = []
        for _, g in df.groupby(df['fecha'].dt.tz_convert('America/New_York').dt.date):
            exp = pd.date_range(g['fecha'].min(), g['fecha'].max(), freq=paso)
            faltan += list(exp.difference(pd.DatetimeIndex(g['fecha'])))
        faltan, exp = pd.DatetimeIndex(faltan), None
    else:
        exp = esperadas(df['fecha'].min(), df['fecha'].max(), paso, o.mercado)
        faltan = exp.difference(pd.DatetimeIndex(df['fecha']))
    n_esp = len(df) + len(faltan)
    p_huecos = len(faltan) / n_esp if n_esp else 0

    vol = df['volume']
    sin_vol = bool(vol.isna().all())
    vol_cero = float((vol == 0).mean()) if not sin_vol else 0.0

    anios = (df['fecha'].max() - df['fecha'].min()).days / 365.25 if len(df) else 0
    eliminadas = (n0 - len(df)) / n0 if n0 else 0
    avisos = []
    if sin_fecha: avisos.append(f'{sin_fecha} filas con fecha ilegible, eliminadas.')
    if dup_iguales: avisos.append(f'{dup_iguales} velas repetidas exactas, eliminadas.')
    if dup_distintas: avisos.append(f'{dup_distintas} velas con la misma fecha y precios distintos: se dejó la primera.')
    if n_imp: avisos.append(f'{n_imp} velas imposibles (precio vacío, cero o máximo/mínimo incoherente), eliminadas.')
    if len(saltos): avisos.append(f'{len(saltos)} saltos fuera de lo normal: revísalos en el gráfico (pueden ser reales).')
    if len(faltan): avisos.append(f'{len(faltan)} velas faltantes ({p_huecos:.1%}). No se rellenaron.'
                                  + (' En bolsa diaria pueden ser festivos.' if o.mercado == 'bolsa' and o.temporalidad == '1d' else ''))
    if sin_vol: avisos.append('La fuente no trae volumen: la columna queda vacía. No uses reglas de volumen.')
    elif vol_cero > 0.2: avisos.append(f'{vol_cero:.0%} de las velas con volumen 0: no uses reglas de volumen.')
    if anios < MIN_ANIOS_APTA: avisos.append(f'Solo {anios:.1f} años de historia: el 30 % fuera de muestra queda corto.')

    if eliminadas > MAX_ELIMINADAS or p_huecos > MAX_HUECOS or anios < MIN_ANIOS or len(df) < 100:
        veredicto = 'NO APTA'
    elif avisos:
        veredicto = 'APTA CON AVISOS'
    else:
        veredicto = 'APTA'

    out = df.copy()
    out['fecha'] = out['fecha'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    out.to_csv(o.salida, index=False)

    L = [f'# Calidad de datos · {o.salida}', '',
         f'Veredicto: **{veredicto}** para backtest', '',
         f'- Origen: {o.crudo} · mercado {o.mercado} · temporalidad {o.temporalidad} · zona original {o.zona}',
         f'- Desde {df["fecha"].min():%Y-%m-%d %H:%M} hasta {df["fecha"].max():%Y-%m-%d %H:%M} UTC · {anios:.1f} años',
         f'- Velas: {n0} en el crudo → {len(df)} curadas ({eliminadas:.1%} eliminadas)',
         f'- Velas faltantes: {len(faltan)} ({p_huecos:.1%})',
         f'- Volumen: {"no viene" if sin_vol else f"{vol_cero:.0%} en cero"}', '',
         '## Avisos'] + ([f'- {x}' for x in avisos] or ['- Ninguno.'])
    if len(saltos):
        L += ['', '## Saltos para revisar (primeros 10)'] + [f'- {f:%Y-%m-%d %H:%M} UTC' for f in list(saltos)[:10]]
    if len(faltan):
        L += ['', '## Velas faltantes (primeras 10)'] + [f'- {pd.Timestamp(f):%Y-%m-%d %H:%M}' for f in list(faltan)[:10]]
    L += ['', 'Umbrales provisionales del Reto: NO APTA si se eliminó más del 5 %, faltan más del 5 % de las velas,',
          'hay menos de 1 año o menos de 100 velas. Datos gratuitos: buenos para investigar, no iguales a datos de pago.']
    open(o.informe, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
