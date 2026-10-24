# robots/ · tu estrategia en código para tu plataforma

Aquí guarda el **agente programador** el código de tu estrategia, desde la fase 03.
Pídeselo al Director: «/programador» o «quiero mi estrategia en Pine Script».

Plataformas: Pine Script (TradingView), MetaTrader 5, NinjaTrader, TradeStation y MultiCharts.
Por cada plataforma salen dos archivos con el nombre de la ficha:
- `robots/nas100_ruptura_ny_pine_estrategia.pine` → opera y se prueba en la plataforma.
- `robots/nas100_ruptura_ny_pine_indicador.pine` → solo dibuja entradas, salidas y stop.

- Tener el código no valida la estrategia: eso lo hacen las fases 04 a 06.
- Primero se prueba en **cuenta demo**. Nunca pongas aquí el número ni la contraseña de tu cuenta.
- Los archivos compilados (`.ex5`, `.eld`, `.pla`, `.dll`) no se suben a GitHub: se generan en tu plataforma.
