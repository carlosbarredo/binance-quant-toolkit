# Quickstart

This path starts offline. It then adds one data source at a time.

## 1. Install

```bash
python -m venv .venv
python -m pip install -e .
```

Activate the environment with the command used by your operating system.

## 2. Discover the catalogue

```bash
bqt catalog
bqt catalog --market usdm
bqt catalog --transport websocket
```

The catalogue says what each dataset measures. It also states a central caveat.

## 3. Run the offline lesson

```bash
bqt demo
```

Expected result: twelve hourly candles, no structural errors, and a small set
of close-to-close statistics. The bundled prices are synthetic teaching data.
Do not treat them as a market record.

## 4. Download candles

```bash
bqt klines BTCUSDT 1m \
  --market usdm \
  --start 2024-01-01T00:00:00Z \
  --end 2024-01-02T00:00:00Z \
  --output data/btcusdt_1m.csv
```

Use `--price-type mark`, `index`, or `premium` for USD-M price families.
Use `--market spot` for Spot trade-price candles.

## 5. Audit before modelling

```bash
bqt audit data/btcusdt_1m.csv --interval 1m --strict
```

Strict mode returns an error when the dataset has a gap, duplicate, invalid
OHLC row, negative volume, negative trade count, or non-monotonic timestamp.

## 6. Add derivatives context

```bash
bqt funding BTCUSDT \
  --start 2024-01-01 \
  --end 2024-02-01 \
  --output data/btcusdt_funding.csv

bqt stats open_interest_history BTCUSDT 5m \
  --output data/btcusdt_open_interest.csv
```

Statistics endpoints are retention-limited. Use archives when the dataset and
date are available there.

## 7. Plan a large archive job

```bash
bqt archive-plan klines BTCUSDT \
  --market um \
  --interval 1m \
  --frequency monthly \
  --start 2023-01-01 \
  --end 2024-01-01
```

Planning makes every expected object visible. Nothing is downloaded.

```bash
bqt archive-download klines BTCUSDT \
  --market um \
  --interval 1m \
  --frequency monthly \
  --start 2023-01-01 \
  --end 2024-01-01 \
  --output-dir data/archives
```

Checksums are verified by default. Missing objects are reported and skipped.
Use `--fail-missing` when complete coverage is mandatory.

## 8. Record live microstructure

Install the optional stream dependency:

```bash
python -m pip install -e .[stream]
```

Record a bounded capture:

```bash
bqt stream \
  --market usdm \
  --streams btcusdt@aggTrade btcusdt@bookTicker btcusdt@depth@100ms \
  --seconds 60 \
  --output data/btcusdt_live.ndjson
```

Use `--messages` instead of, or together with, `--seconds`. The command rejects
an unbounded capture. Disk growth must be an explicit decision.

## What to learn next

- Read [Choosing data](CHOOSING_DATA.md).
- Read [Order-book reconstruction](ORDER_BOOK.md) before using depth deltas.
- Read [Methodology](METHODOLOGY.md) before joining or backtesting datasets.
- Use [Research recipes](RECIPES.md) as starting points, not finished strategies.

