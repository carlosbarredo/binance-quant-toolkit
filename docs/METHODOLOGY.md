# Research methodology

The downloader solves acquisition. It does not solve research design.

## A defensible pipeline

1. Write the hypothesis before inspecting the holdout.
2. Name the market, symbol universe, contract type and price family.
3. Fix the event clock and the earliest observable timestamp.
4. Download immutable raw inputs. Preserve checksums and metadata.
5. Audit gaps, duplicates, schema drift and impossible values.
6. Build features with past information only.
7. Model fees, spread, slippage, funding, latency and position limits.
8. Split time in order. Fit on the past. Evaluate on the future.
9. Test parameter, universe and regime stability.
10. Report failures and negative results.

## Joining sources

Prefer backward as-of joins. A feature row may use only a source value available
at or before the decision time. Set a maximum staleness. Never forward-fill
through an unexplained outage. Record the original source timestamp after every
join so availability can be audited.

## Candle backtests

One candle cannot tell whether its high or low happened first. A strategy that
touches both a stop and a target inside one bar is path-dependent. Use finer data,
a conservative rule, or mark the outcome ambiguous. Never choose the favourable
ordering after seeing the result.

## Funding

Separate announced estimates, realised rates and cash-flow application. A value
published after the decision cannot become a feature for that decision. Apply
funding only when the simulated position is eligible at the relevant timestamp.

## Multiple testing

Trying many symbols, windows and rules creates selection bias. Keep an experiment
ledger. Count failed variants. Reserve a final untouched period. A high in-sample
ratio is not evidence of a deployable edge.

## Reproducibility record

Store code revision, request parameters, source object names, checksum status,
download time, timezone, package versions and quality report. A result that
cannot be rebuilt should not be promoted to a strategy conclusion.

