# Binance Quant Toolkit

**A research-first data toolkit for quant traders.**

Download historical candles and trades. Plan verified public-archive jobs.
Capture live order flow. Bootstrap and validate an order book. Add funding,
mark price, open interest and positioning context. Audit the result before it
reaches a model.

[Versión en español](README_ES.md) · [Quickstart](docs/QUICKSTART.md) ·
[Data catalogue](DATA.md) · [Choosing data](docs/CHOOSING_DATA.md) ·
[Methodology](docs/METHODOLOGY.md) · [Notebook](notebooks/binance_quant_toolkit_en.ipynb)

> Public market data only. No orders. No API keys. No profit claims.
> Research and education, not investment advice.

## What you can collect

| Area | Datasets |
| --- | --- |
| Price bars | Trade, mark, index and premium-index klines |
| Trades | Aggregate trades, individual trades and live trade streams |
| Order book | REST snapshots, best bid/ask, partial depth and diff depth |
| Perpetuals | Realised funding, live mark/index context and funding estimates |
| Positioning | Open interest, global ratios, top-trader ratios and taker ratio |
| Curve and stress | Basis, forced-order events and archive liquidation snapshots |
| Bulk history | Daily and monthly public ZIP archives with SHA-256 checks |

Supported live/API markets are Spot and USD-M futures. The archive planner also
supports COIN-M paths. Each family has different history and semantics. The
repository explains those differences instead of hiding them behind one method.

## Three acquisition paths

```text
REST                  Public archive             WebSocket
small ranges          months or years            live events
current snapshots     immutable ZIP objects      exchange + receipt clocks
normalised tables     checksum verification      raw NDJSON capture
        \                    |                    /
         \                   |                   /
          quality checks -> provenance -> research tables
```

Use REST for bounded queries. Use archives for large history. Use WebSocket when
event order or local receipt time matters. Use a REST snapshot together with
diff-depth events to reconstruct a book.

## Start offline

```bash
python -m pip install -e .
bqt catalog
bqt demo
```

The demo uses a bundled synthetic dataset. It needs no network connection.

## Download examples

Trade-price candles:

```bash
bqt klines BTCUSDT 1m \
  --market usdm \
  --start 2024-01-01 \
  --end 2024-01-02 \
  --output data/btcusdt_1m.csv
```

Mark-price candles use the same interface:

```bash
bqt klines BTCUSDT 5m \
  --market usdm \
  --price-type mark \
  --start 2024-01-01 \
  --end 2024-02-01 \
  --output data/btcusdt_mark_5m.parquet
```

Realised funding and current depth:

```bash
bqt funding BTCUSDT \
  --start 2024-01-01 \
  --end 2024-02-01 \
  --output data/btcusdt_funding.csv

bqt depth BTCUSDT --market usdm --limit 1000 \
  --output data/btcusdt_depth.csv
```

The range is half-open: `start <= event_time < end`. Dates without an offset
are UTC. CSV works with the base install. Parquet needs `pip install -e .[parquet]`.

## Download large histories

Inspect the exact archive objects first:

```bash
bqt archive-plan klines BTCUSDT \
  --market um --interval 1m --frequency monthly \
  --start 2023-01-01 --end 2024-01-01
```

Then download them:

```bash
bqt archive-download klines BTCUSDT \
  --market um --interval 1m --frequency monthly \
  --start 2023-01-01 --end 2024-01-01 \
  --output-dir data/archives
```

Checksums are enabled. Missing objects are visible. Existing ZIPs are reused.
Archives remain raw by design. Extraction and transformation are separate steps.

## Capture live microstructure

```bash
python -m pip install -e .[stream]

bqt stream \
  --market usdm \
  --streams btcusdt@aggTrade btcusdt@bookTicker btcusdt@depth@100ms \
  --seconds 60 \
  --output data/btcusdt_live.ndjson
```

Every line stores the original payload and a local nanosecond receipt timestamp.
Captures must have a time or message limit. Accidental unbounded disk growth is
rejected. Read [Order-book reconstruction](docs/ORDER_BOOK.md) before applying
depth updates.

## Python API

```python
from binance_quant_toolkit import BinanceRestClient, KlineRequest, audit_klines

request = KlineRequest(
    symbol="BTCUSDT",
    interval="5m",
    start="2024-01-01",
    end="2024-01-08",
    market="usdm",
    price_type="trade",
)

with BinanceRestClient() as client:
    candles = client.fetch_klines(request)
    funding = client.fetch_funding_rates("BTCUSDT", request.start, request.end)
    depth = client.depth_snapshot("usdm", "BTCUSDT", limit=1_000)

report = audit_klines(
    candles,
    "5m",
    start=request.start,
    end=request.end,
)
report.require_clean()
```

## Quality is part of the product

The kline audit checks:

- missing and duplicate open times;
- timestamp order;
- positive prices and valid OHLC geometry;
- non-negative volume and trade counts;
- edge gaps when the expected range is supplied.

The REST client adds UTC parsing, cursor pagination, timeouts, status handling,
bounded exponential backoff and stable typed schemas. CLI exports add a metadata
sidecar. Archive downloads can verify SHA-256. Local order books reject sequence
gaps and crossed state.

## Choose data from the mechanism

- Trend and cross-sectional work often starts with candles.
- Carry needs realised funding plus mark, index and premium context.
- Order flow needs trades. Execution research also needs spread and depth.
- Market making needs ordered book deltas, snapshots and latency clocks.
- Crowding studies add open interest and positioning ratios.
- Stress studies add mark price, trade flow, depth and forced orders.

More data is not automatically better. Each additional source adds a clock,
retention rule and failure mode. [Choosing data](docs/CHOOSING_DATA.md) maps common
research questions to the smallest useful dataset.

## Important boundaries

- A candle hides the intrabar path.
- Aggregate trades are not raw individual ticks.
- Mark and index prices are not executable trade prices.
- A depth snapshot is not a historical order book.
- WebSocket deltas need sequence reconciliation.
- Funding, ratios and archive metrics can create look-ahead when aligned badly.
- Clean history does not prove alpha or future profitability.

## Repository map

```text
src/binance_quant_toolkit/   REST, archive, streams, schemas, quality and storage
tests/                       Network-free unit and behavioural tests
examples/                    Offline sample, bundle download and local-book lesson
notebooks/                   Short bilingual learning notebooks
docs/                        Data choice, methodology, order book and research recipes
.github/workflows/           inactive template for explicitly approved one-off checks
```

## Reproduce

```bash
python -m pip install -e .[dev]
pytest
ruff check .
```

Optional features:

```bash
python -m pip install -e .[all]
jupyter lab notebooks/
```

## From the original notebook to 1.0

The 2023 repository contained one request for one candle page. It used a
machine-dependent time conversion. It did not check status, paginate, retry or
audit the response. Version 1.0 keeps the useful educational intention and
rebuilds the implementation around explicit contracts and reproducible inputs.

See [`CHANGELOG.md`](CHANGELOG.md) and [`CITATION.cff`](CITATION.cff).
Apache-2.0 applies to the repository code and documentation. Binance is a
third-party service and is not affiliated with this project.

GitHub Actions is intentionally disabled by default. This repository is a public distribution and archival surface; routine verification runs locally.

