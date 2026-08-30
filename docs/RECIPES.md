# Research recipes

These recipes specify datasets and checks. They do not prescribe trades.

## Funding and basis panel

Collect trade klines, mark klines, index klines, premium klines and realised
funding. Align backward to the decision clock. Keep the raw funding timestamp.
Compare gross carry with fees, spread, hedge slippage and capital constraints.

## Order-flow bar

Collect aggregate trades. Classify signed quantity from the maker-side flag.
Build fixed-time, volume or dollar bars. Add book ticker for contemporaneous
spread. Test whether results survive a latency shift and larger trade aggregation.

## Crowding regime

Collect price, open interest, global ratios, top-trader ratios and taker ratio.
Measure changes, not only levels. Audit retention. Avoid treating missing early
history as zero. Validate the definition separately for each ratio.

## Liquidation stress window

Record forced-order events, trade flow, mark price and depth. Create event windows
using exchange time. Keep receipt time for latency analysis. Treat forced-order
coverage as sampled unless completeness is independently established.

## Cross-market dislocation

Collect Spot trade price, perpetual trade price, mark price and index price on a
common clock. Model different fees and fill mechanisms. Reject joins that exceed
the staleness limit. Report both raw and executable spread assumptions.

