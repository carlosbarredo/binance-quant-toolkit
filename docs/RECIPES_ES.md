# Recetas de investigación

Estas recetas definen datos y controles. No recomiendan operaciones.

## Panel de funding y basis

Combina velas de trade, mark, index, premium y funding realizado. Alinea hacia
atrás respecto al instante de decisión. Conserva el timestamp original. Compara
el carry bruto con fees, spread, slippage de cobertura y capital.

## Barras de flujo

Captura trades agregados. Asigna signo con el maker flag. Construye barras de
tiempo, volumen o notional. Añade book ticker para el spread. Comprueba si el
resultado sobrevive a más latencia y a otra agregación.

## Régimen de crowding

Combina precio, open interest, ratios globales, top traders y taker ratio. Estudia
cambios además de niveles. No conviertas historia ausente en ceros. Valida por
separado la definición de cada ratio.

## Ventana de liquidaciones

Captura eventos forzados, trades, mark y profundidad. Construye ventanas con
tiempo del exchange. Conserva el tiempo de recepción. Considera la cobertura
muestreada salvo que puedas demostrar que es completa.

## Dislocación entre mercados

Combina spot, perpetuo, mark e index con un reloj común. Modela fees y ejecución
por separado. Rechaza uniones demasiado antiguas. Publica tanto el spread crudo
como el ejecutable bajo tus supuestos.

