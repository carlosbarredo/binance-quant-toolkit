# Choosing data for a strategy idea

Start with the question. Do not start with the easiest endpoint.

| Research question | Minimum useful data | Better context | Main trap |
| --- | --- | --- | --- |
| Medium-term trend | Trade klines | Mark/index klines, funding | Treating one bar frequency as robust |
| Cross-sectional momentum | Synchronous klines | Listing history, volume filters | Survivorship and asynchronous starts |
| Volatility breakout | Fine klines or trades | Spread and depth | Assuming a bar high was executable |
| Funding carry | Realised funding | Mark, index, premium, fees | Using the next published rate too early |
| Basis or calendar spread | Mark/index or contract prices | Funding and maturity | Mixing timestamps or contract definitions |
| Order-flow signal | Aggregate or raw trades | Book ticker, diff depth | Confusing maker flag with buyer intent |
| Market making | Diff depth and trades | Snapshot, latency clocks | Ignoring queue position and cancellations |
| Liquidation cascade | Forced-order stream | Trades, mark, depth | Treating sampled events as a complete ledger |
| Crowding filter | OI and long/short ratios | Price and taker ratio | Treating an account ratio as dollar exposure |
| Execution cost | Book and trades | Receipt time and fee schedule | Filling at displayed size with zero latency |

## Resolution is a modelling choice

More rows do not guarantee more information. Fine data adds microstructure noise,
storage cost and sequence risk. Coarse data removes the path that determines
stops and fills. Select the lowest resolution that preserves the mechanism you
want to study. Keep a finer sample for sensitivity checks.

## Trade, mark and index prices answer different questions

- Trade price describes matched exchange transactions.
- Mark price supports risk and liquidation logic.
- Index price represents the exchange's external reference basket.
- Premium index describes a component related to perpetual funding.

Do not splice them into one price series without a named transformation.

## REST, archive or stream

REST is ideal for small panels and current snapshots. Archives are better for
large history. Streams are required when message order, local receipt time or
live book state matters. A serious project often uses all three.

