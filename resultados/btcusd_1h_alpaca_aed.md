=================================================================
AED - BTCUSD_1H_ALPACA.CSV
=================================================================

PARTICION
  DISENO:     2021-10-27 -> 2024-08-14  24547 velas  H1
  EXAMEN:     2024-08-14 -> 2025-10-27  10521 velas  [sellado]
  VALIDACION: 2025-10-27 -> 2026-10-27  8768 velas  [sellado]
  Anos diseno: 2.8   Familia: RANGO  comprar abajo, vender arriba

00 - CALIDAD DE DATOS
  Veredicto: APTA CON AVISOS
  43.836 velas totales  |  Saltos raros  |  5 anos de historia

01 - LINEA BASE
  Velas que suben:           50.6%
  Rango vela normal (H-L):   0.82%  (82 pb)
  Movimiento medio (|c-c|):  0.36%  (36 pb)

  TENDENCIA DE FONDO
  Retorno total diseno:      -2.6%  perdio
  CAGR anual:                -0.92%  LATERAL
  Tiempo sobre MA200:        47.8%  sin sesgo
  Caida maxima buy&hold:     -77.2%

03 - TEMPERAMENTO
  Volatilidad en racimos:    0.29
  Colas gordas (curtosis):   13.6  (7.7x normal)
  Asimetria:                 0.036
  Peor / mejor vela:         -7.1% / 6.8%
  Volatilidad anualizada:    55.3%
  Vol. al final diseno:      66.6%  (mediana: 51%)  REGIMEN ALTO
  Autocorr lag 1:            -0.0066  dentro del ruido
  Kaufman ER mediana:        0.194  ZIGZAG (55% del tiempo)

02 - HALLAZGOS  (la vela siguiente frente a una cualquiera)
  Linea base: 0.0016%
  SEMAFORO     HALLAZGO                                  RETORNO
  --------------------------------------------------------------
  CLARA        La vela de las 01h                         -0.048%
  CLARA        La vela de las 22h                         +0.040%
  CLARA        La vela de las 20h                         +0.042%
  SE INSINUA   La vela de las 10h                         +0.028%
  SE INSINUA   La vela de las 19h                         -0.031%
  ver los 20 hallazgos sin senal (NADA)

04 - FUNCIONA CON UNA MEDIA MOVIL?  ->  MIXTO
  Comprar y aguantar diseno: -2.6%
  MEDIA         OPS/ANO       PF  LECTURA
  --------------------------------------
  Media 20         559.3     1.02  A MEDIAS
  Media 50         342.7     1.02  A MEDIAS
  Media 100        234.1     1.02  A MEDIAS
  Media 200        144.7     1.01  A MEDIAS

05 - COSTES DEL BROKER  ->  NO PASA EL 10%
  Entrar y salir cuesta: 15 pb
  Una vela normal mueve: 36 pb
  El coste se come:      41.2% de una vela  (limite 10%)
  Swap dormir comprado:  -3.01 pb/noche
  Swap dormir vendido:   3.01 pb/noche

MAPA DEL ACTIVO
  1. Tendencia de fondo:  LATERAL  (-0.92% anual)
  2. Dia a dia:           REVIERTE  (autocorr -0.007, Kaufman 0.194)
  3. Familia a probar:    RANGO: comprar abajo, vender arriba

ESTRATEGIAS DOCUMENTADAS
  RSI 30/70  (Wilder 1978)
  Bandas de Bollinger  (Bollinger 2001)
  RSI(2)  (Connors & Alvarez 2008)