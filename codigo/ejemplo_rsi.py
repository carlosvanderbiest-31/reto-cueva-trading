"""
Ejemplo de estrategia personalizada para usar con optimizar.py
RSI simple: largo cuando RSI < sobrevendido, corto cuando RSI > sobrecomprado

Uso:
  python codigo/optimizar.py \
    --csv datos/btcusdt_1d_binance.csv \
    --tipo codigo/ejemplo_rsi.py \
    --barrido "periodo=7:28:7,sobrecomprado=65:80:5"

La funcion generar_senales(df, **params) es lo unico obligatorio.
"""
import numpy as np
import pandas as pd


def _rsi(close: pd.Series, periodo: int) -> pd.Series:
    delta  = close.diff()
    ganancia = delta.clip(lower=0).ewm(com=periodo - 1, adjust=False).mean()
    perdida  = (-delta.clip(upper=0)).ewm(com=periodo - 1, adjust=False).mean()
    rs  = ganancia / perdida.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def generar_senales(df: pd.DataFrame, periodo: int = 14,
                    sobrecomprado: float = 70, **_) -> np.ndarray:
    """
    +1 cuando RSI < (100 - sobrecomprado)  → zona sobrevendida → largo
    -1 cuando RSI > sobrecomprado          → zona sobrecomprada → corto
    Mantiene la ultima senal hasta que cambia (always-in).
    """
    close = pd.Series(df["close"].values.astype(float))
    rsi   = _rsi(close, int(periodo))
    sobrevendido = 100 - sobrecomprado

    signals = np.zeros(len(df))
    pos     = 0.0
    for i in range(len(df)):
        if np.isnan(rsi.iloc[i]):
            signals[i] = 0.0
            continue
        if rsi.iloc[i] < sobrevendido:
            pos = 1.0
        elif rsi.iloc[i] > sobrecomprado:
            pos = -1.0
        signals[i] = pos

    # Rellenar ceros al inicio con primera senal valida (neutro = sin posicion = 1.0 por defecto)
    first_valid = next((i for i, s in enumerate(signals) if s != 0), None)
    if first_valid is not None and first_valid > 0:
        signals[:first_valid] = signals[first_valid]
    if np.all(signals == 0):
        signals[:] = 1.0

    return signals
