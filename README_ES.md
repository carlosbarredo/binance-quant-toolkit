# Binance Quant Toolkit

**Un toolkit de datos pensado para quant traders.**

Descarga velas y trades históricos. Planifica archivos públicos verificados.
Captura order flow en vivo. Reconstruye y valida un order book. Añade funding,
mark price, open interest y posicionamiento. Audita todo antes de modelar.

[English](README.md) · [Inicio rápido](docs/QUICKSTART_ES.md) ·
[Catálogo de datos](DATA.md) · [Cómo elegir](docs/CHOOSING_DATA_ES.md) ·
[Metodología](docs/METHODOLOGY_ES.md) · [Notebook](notebooks/binance_quant_toolkit_es.ipynb)

> Solo datos públicos. Sin órdenes. Sin claves API. Sin promesas de rentabilidad.
> Investigación y formación. No es asesoramiento financiero.

## Qué puedes recoger

| Área | Datasets |
| --- | --- |
| Barras | Velas de trade, mark, index y premium index |
| Trades | Agregados, individuales y streams en vivo |
| Order book | Snapshots, bid/ask, profundidad parcial y deltas |
| Perpetuos | Funding realizado y contexto de mark e index |
| Posicionamiento | Open interest, ratios globales, top traders y taker ratio |
| Curva y estrés | Basis, órdenes forzadas y snapshots de liquidaciones |
| Histórico masivo | ZIP diarios y mensuales con SHA-256 |

La API y los streams cubren Spot y futuros USD-M. El planificador de archivos
también cubre rutas COIN-M. Cada familia tiene otra historia y otro significado.
El repositorio explica esas diferencias. No las esconde bajo un único método.

## Tres vías de adquisición

```text
REST                  Archivo público            WebSocket
rangos pequeños       meses o años               eventos en vivo
snapshots actuales    ZIP inmutables             reloj exchange + recepción
tablas normalizadas   checksum                    NDJSON crudo
        \                    |                    /
         \                   |                   /
          calidad -> procedencia -> tablas de investigación
```

Usa REST para consultas acotadas. Usa archivos para históricos grandes. Usa
WebSocket si importa el orden de eventos o la hora local de recepción. Para
reconstruir el book, combina un snapshot REST con deltas de profundidad.

## Empieza offline

```bash
python -m pip install -e .
bqt catalog
bqt demo
```

La demostración usa datos sintéticos incluidos. No necesita conexión.

## Ejemplos de descarga

Velas basadas en trades:

```bash
bqt klines BTCUSDT 1m \
  --market usdm \
  --start 2024-01-01 \
  --end 2024-01-02 \
  --output data/btcusdt_1m.csv
```

Velas de mark price:

```bash
bqt klines BTCUSDT 5m \
  --market usdm \
  --price-type mark \
  --start 2024-01-01 \
  --end 2024-02-01 \
  --output data/btcusdt_mark_5m.parquet
```

Funding realizado y profundidad actual:

```bash
bqt funding BTCUSDT \
  --start 2024-01-01 \
  --end 2024-02-01 \
  --output data/btcusdt_funding.csv

bqt depth BTCUSDT --market usdm --limit 1000 \
  --output data/btcusdt_depth.csv
```

El rango es semiabierto: `inicio <= tiempo < fin`. Las fechas sin offset son UTC.
CSV funciona con la instalación base. Parquet necesita `pip install -e .[parquet]`.

## Históricos grandes

Mira primero los objetos exactos:

```bash
bqt archive-plan klines BTCUSDT \
  --market um --interval 1m --frequency monthly \
  --start 2023-01-01 --end 2024-01-01
```

Después descárgalos:

```bash
bqt archive-download klines BTCUSDT \
  --market um --interval 1m --frequency monthly \
  --start 2023-01-01 --end 2024-01-01 \
  --output-dir data/archives
```

El checksum está activo. Los objetos ausentes se ven. Los ZIP existentes se
reutilizan. El archivo crudo no se transforma durante la descarga.

## Microestructura en vivo

```bash
python -m pip install -e .[stream]

bqt stream \
  --market usdm \
  --streams btcusdt@aggTrade btcusdt@bookTicker btcusdt@depth@100ms \
  --seconds 60 \
  --output data/btcusdt_live.ndjson
```

Cada línea conserva el payload y un timestamp local en nanosegundos. Toda
captura necesita límite de tiempo o mensajes. Lee [Reconstrucción del order
book](docs/ORDER_BOOK_ES.md) antes de aplicar deltas.

## API de Python

```python
from binance_quant_toolkit import BinanceRestClient, KlineRequest, audit_klines

peticion = KlineRequest(
    "BTCUSDT",
    "5m",
    "2024-01-01",
    "2024-01-08",
    "usdm",
    "trade",
)

with BinanceRestClient() as cliente:
    velas = cliente.fetch_klines(peticion)
    funding = cliente.fetch_funding_rates("BTCUSDT", peticion.start, peticion.end)
    profundidad = cliente.depth_snapshot("usdm", "BTCUSDT", limit=1_000)

informe = audit_klines(
    velas,
    "5m",
    start=peticion.start,
    end=peticion.end,
)
informe.require_clean()
```

## La calidad forma parte del producto

La auditoría comprueba huecos, duplicados, orden temporal, geometría OHLC,
precios positivos, volumen y trades no negativos. Si recibe el rango esperado,
también detecta huecos en los bordes.

El cliente añade UTC explícito, paginación, timeouts, estados HTTP, reintentos
acotados y esquemas estables. Los exports incluyen metadatos. Los archivos
verifican SHA-256. El order book local rechaza huecos y estados cruzados.

## Elige los datos desde el mecanismo

- Tendencia y cross-section suelen empezar con velas.
- Carry necesita funding y contexto de mark, index y premium.
- Order flow necesita trades. Ejecución añade spread y profundidad.
- Market making necesita deltas ordenados, snapshot y relojes de latencia.
- Crowding añade open interest y ratios.
- Estrés añade mark, trades, profundidad y órdenes forzadas.

Más datos no siempre es mejor. Cada fuente añade un reloj, una retención y un
modo de fallo. [Cómo elegir datos](docs/CHOOSING_DATA_ES.md) parte de la pregunta.

## Límites importantes

- Una vela esconde el camino intrabar.
- Un trade agregado no es un tick individual.
- Mark e index no son precios ejecutables.
- Un snapshot no es un histórico del book.
- Los deltas necesitan reconciliar su secuencia.
- Funding y ratios pueden crear look-ahead si se alinean mal.
- Un histórico limpio no demuestra alpha.

## Estructura

```text
src/binance_quant_toolkit/   REST, archivos, streams, esquemas y calidad
tests/                       Pruebas sin red
examples/                    Muestra, bundle y lección de order book
notebooks/                   Recorrido breve y bilingüe
docs/                        Elección, método, order book y recetas
.github/workflows/           plantilla inactiva para comprobaciones puntuales autorizadas
```

## Reproducir

```bash
python -m pip install -e .[dev]
pytest
ruff check .
```

Para instalar todo:

```bash
python -m pip install -e .[all]
jupyter lab notebooks/
```

El repositorio de 2023 contenía una petición para una página de velas. No
paginaba, no validaba, no reintentaba y dependía de la zona horaria del equipo.
La versión 1.0 conserva la intención didáctica y rehace toda la implementación.

Consulta [`CHANGELOG.md`](CHANGELOG.md) y [`CITATION.cff`](CITATION.cff).
Licencia Apache-2.0. Binance es un servicio externo no afiliado al proyecto.

GitHub Actions está desactivado por defecto. Este repositorio funciona como escaparate público y archivo; la verificación habitual se ejecuta localmente.

