# Data contract and source map

This file is the compact contract for every dataset exposed by the toolkit.
Read it before joining sources or writing a backtest.

## Source selection

| Need | Preferred source | Reason |
| --- | --- | --- |
| A small historical window | REST | Simple and immediately normalised |
| Months or years of event data | Public archive | Efficient and reproducible ZIP objects |
| Current book state | REST depth snapshot | Provides the bootstrap update ID |
| Reconstructable live order book | REST snapshot + WebSocket diff depth | Snapshot gives state; deltas give change |
| Live trades or quotes | WebSocket | Lower overhead than repeated polling |
| A bounded research capture | WebSocket recorder | NDJSON preserves the original payload and receipt time |

REST endpoints have limits and retention rules. Archives can have missing days.
WebSocket collection starts now; it cannot recover events sent before connection.

## Dataset families

| Key | Markets | Sources | Core fields | Common research use |
| --- | --- | --- | --- | --- |
| `klines` | Spot, USD-M | REST, archive, stream | OHLCV, trades, taker volume | Trend, volatility, cross-sectional factors |
| `mark_klines` | USD-M | REST, archive | Mark OHLC | Liquidation-aware and basis research |
| `index_klines` | USD-M | REST, archive | Index OHLC | Venue dislocation and basis |
| `premium_klines` | USD-M | REST, archive | Premium-index OHLC | Funding and carry models |
| `agg_trades` | Spot, USD-M | REST, archive, stream | Price, quantity, IDs, maker side | Order flow, volume bars, impact |
| `trades` | Spot, USD-M | Archive, stream | Individual trade fields | Tick rules and microstructure |
| `depth_snapshot` | Spot, USD-M | REST | Price levels, size, update ID | Spread, depth, book bootstrap |
| `depth_diff` | Spot, USD-M | Stream | Changed levels and sequence IDs | Local book and imbalance |
| `book_ticker` | Spot, USD-M | REST, archive, stream | Best bid/ask and size | Spread and execution models |
| `funding_rate` | USD-M | REST, archive | Realised rate, time, mark | Carry and holding-cost models |
| `open_interest_history` | USD-M | REST, archive metrics | Contracts, value, timestamp | Leverage and regime context |
| positioning ratios | USD-M | REST | Long/short ratios | Crowding and sentiment |
| `taker_ratio` | USD-M | REST | Buy/sell volume and ratio | Aggressor flow |
| `basis` | USD-M | REST | Basis and annualised basis | Curve and calendar spreads |
| `liquidations` | USD-M | Stream, archive | Forced-order event | Stress and cascade studies |

Run `bqt catalog` for caveats and strategy uses at the command line.

## Canonical kline schema

| Column | Type | Meaning |
| --- | --- | --- |
| `open_time` | UTC datetime | Candle start; primary key with symbol and interval |
| `open`, `high`, `low`, `close` | float64 | Prices for the selected price family |
| `volume` | float64 | Base-asset volume for trade-price candles |
| `close_time` | UTC datetime | Exchange candle close boundary |
| `quote_volume` | float64 | Quote-asset notional volume |
| `trade_count` | nullable integer | Number of trades contributing to the candle |
| `taker_buy_base_volume` | float64 | Base volume attributed to taker buys |
| `taker_buy_quote_volume` | float64 | Quote volume attributed to taker buys |
| `ignore` | nullable integer | Exchange compatibility field; do not model it |

The request range is half-open: `start <= open_time < end`. Naive dates are UTC.
The client sorts by `open_time` and removes duplicate open times after pagination.
The audit still detects duplicates in files loaded from elsewhere.

## Event-time rules

Keep these clocks separate:

- **Exchange event time:** when Binance says the event occurred.
- **Transaction time:** when the matching engine processed the update, if supplied.
- **Receipt time:** when this recorder received the message locally.
- **Publication availability:** when a historical row could first have been observed.

Do not substitute one clock for another. A clean merge can still contain
look-ahead if a value is aligned before it became observable.

## Storage

CSV is portable and inspectable. Parquet is smaller and preserves types better.
Parquet support is optional. Every CLI export writes a JSON metadata sidecar.
It records the dataset, market, symbol and row count. Keep that file with the data.

WebSocket captures use NDJSON. Each line is independent JSON. It contains a
nanosecond local receipt timestamp, market name and original combined payload.

## Known limits

- A candle is an aggregation. Its high-low path is unknown.
- Aggregate trades are not identical to individual trade ticks.
- A depth snapshot does not show events between snapshots.
- Diff-depth messages require strict sequence reconciliation.
- Funding time is not a trade execution timestamp.
- Positioning ratios describe exchange-defined populations.
- REST statistics often have short retention.
- Archive coverage varies by dataset, market, symbol and date.
- Archive timestamp units can change across eras. Inspect the raw header and magnitude.
- Official archives can contain gaps or duplicates. Always audit them.
- Symbols can be listed, delisted or migrated.
