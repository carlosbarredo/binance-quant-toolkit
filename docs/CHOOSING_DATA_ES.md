# Cómo elegir datos para una estrategia

Empieza por la pregunta. No empieces por el endpoint más cómodo.

| Pregunta | Datos mínimos | Contexto mejor | Riesgo principal |
| --- | --- | --- | --- |
| Tendencia | Velas de trades | Mark, index y funding | Confiar en una sola frecuencia |
| Momentum transversal | Velas sincronizadas | Listados y filtro de volumen | Sesgo de supervivencia |
| Ruptura de volatilidad | Velas finas o trades | Spread y profundidad | Suponer ejecutable el máximo de una vela |
| Carry de funding | Funding realizado | Mark, index, premium y fees | Usar antes de tiempo la siguiente tasa |
| Basis | Precio de contrato e índice | Funding y vencimiento | Mezclar timestamps o contratos |
| Flujo de órdenes | Trades agregados o ticks | Book ticker y profundidad | Interpretar mal el maker flag |
| Market making | Profundidad y trades | Snapshot y relojes | Ignorar cola, cancelaciones y latencia |
| Liquidaciones | Stream forzado | Trades, mark y profundidad | Creer completo un stream muestreado |
| Crowding | OI y ratios long/short | Precio y taker ratio | Tratar cuentas como exposición monetaria |
| Coste de ejecución | Book y trades | Recepción y comisiones | Llenar todo sin latencia ni cola |

## La resolución forma parte del modelo

Más filas no garantizan más información. Los datos finos añaden ruido, coste de
almacenamiento y riesgo de secuencia. Los datos gruesos eliminan el camino que
determina stops y fills. Elige la resolución más baja que conserve el mecanismo.
Mantén otra más fina para comprobar sensibilidad.

## Trade, mark e index responden preguntas distintas

- Trade price describe operaciones cruzadas.
- Mark price apoya la lógica de riesgo y liquidación.
- Index price representa la referencia externa del exchange.
- Premium index recoge un componente vinculado al funding perpetuo.

No los unas en una única serie sin nombrar la transformación.

