"""Human-readable catalogue of supported public market datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    market: str
    transport: str
    description: str
    typical_uses: tuple[str, ...]
    caveat: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_SPECS = (
    DatasetSpec(
        "klines",
        "spot/usdm",
        "REST/archive/WebSocket",
        "Trade-price OHLCV candles.",
        ("signals", "backtests", "volatility"),
        "Candles hide intrabar path and queue dynamics.",
    ),
    DatasetSpec(
        "mark_klines",
        "usdm",
        "REST/archive",
        "Mark-price candles.",
        ("liquidation-aware research", "PnL approximation"),
        "Mark price is not an executable trade price.",
    ),
    DatasetSpec(
        "index_klines",
        "usdm",
        "REST/archive",
        "Underlying index-price candles.",
        ("basis", "dislocation studies"),
        "Index methodology can change.",
    ),
    DatasetSpec(
        "premium_klines",
        "usdm",
        "REST/archive",
        "Premium-index candles.",
        ("funding models", "basis"),
        "Do not confuse premium with realised funding.",
    ),
    DatasetSpec(
        "agg_trades",
        "spot/usdm",
        "REST/archive/WebSocket",
        "Trades aggregated by matching-engine rules.",
        ("order flow", "volume bars", "microstructure"),
        "Aggregation is not raw tick-by-tick trade history.",
    ),
    DatasetSpec(
        "trades",
        "spot/usdm",
        "REST/archive/WebSocket",
        "Individual public trades.",
        ("tick studies", "trade classification"),
        "Large histories should use archives, not REST.",
    ),
    DatasetSpec(
        "depth_snapshot",
        "spot/usdm",
        "REST",
        "Point-in-time order-book snapshot.",
        ("spread", "depth", "book bootstrap"),
        "One snapshot does not describe the intervening path.",
    ),
    DatasetSpec(
        "depth_diff",
        "spot/usdm",
        "WebSocket",
        "Incremental order-book updates.",
        ("local book", "imbalance", "impact models"),
        "Sequence IDs must be reconciled with a REST snapshot.",
    ),
    DatasetSpec(
        "partial_depth",
        "spot/usdm",
        "WebSocket",
        "Top book levels at a fixed cadence.",
        ("top-of-book depth", "monitoring"),
        "Not a full reconstructable book.",
    ),
    DatasetSpec(
        "book_ticker",
        "spot/usdm",
        "REST/archive/WebSocket",
        "Best bid, ask and displayed sizes.",
        ("spread", "mid-price", "execution simulation"),
        "Top of book omits deeper liquidity.",
    ),
    DatasetSpec(
        "funding_rate",
        "usdm",
        "REST/archive",
        "Realised perpetual funding rates.",
        ("carry", "funding arbitrage", "cost models"),
        "Publication and payment timestamps must not be used with look-ahead.",
    ),
    DatasetSpec(
        "mark_price",
        "usdm",
        "REST/WebSocket",
        "Live mark, index and next funding context.",
        ("monitoring", "basis", "liquidation research"),
        "A live observation is not a historical series.",
    ),
    DatasetSpec(
        "open_interest",
        "usdm",
        "REST",
        "Current contract open interest.",
        ("leverage context", "positioning"),
        "The current endpoint is only a snapshot.",
    ),
    DatasetSpec(
        "open_interest_history",
        "usdm",
        "REST/archive",
        "Periodic open-interest statistics.",
        ("positioning factors", "regime filters"),
        "REST history is retention-limited; archives can contain gaps.",
    ),
    DatasetSpec(
        "global_long_short_ratio",
        "usdm",
        "REST",
        "Global account long/short ratio.",
        ("sentiment", "crowding"),
        "Account ratio is not capital-weighted exposure.",
    ),
    DatasetSpec(
        "top_account_ratio",
        "usdm",
        "REST",
        "Top-trader account long/short ratio.",
        ("crowding", "contrarian studies"),
        "The top-trader population is exchange-defined.",
    ),
    DatasetSpec(
        "top_position_ratio",
        "usdm",
        "REST",
        "Top-trader position long/short ratio.",
        ("positioning", "crowding"),
        "Historical retention is limited.",
    ),
    DatasetSpec(
        "taker_ratio",
        "usdm",
        "REST",
        "Taker buy/sell volume ratio.",
        ("aggressor flow", "short-horizon signals"),
        "Aggressor flow alone does not measure price impact.",
    ),
    DatasetSpec(
        "basis",
        "usdm",
        "REST",
        "Contract basis statistics.",
        ("curve", "carry", "calendar spreads"),
        "Compare like-for-like maturities and timestamps.",
    ),
    DatasetSpec(
        "liquidations",
        "usdm",
        "WebSocket/archive",
        "Forced-order events or snapshots.",
        ("stress events", "cascade analysis"),
        "The stream can be sampled and is not a complete private liquidation ledger.",
    ),
    DatasetSpec(
        "metrics",
        "usdm",
        "archive",
        "Bundled futures positioning metrics.",
        ("broad factor panels", "open-interest research"),
        "Audit missing and duplicate timestamps before use.",
    ),
)


def list_datasets(*, market: str | None = None, transport: str | None = None) -> list[DatasetSpec]:
    """Return catalogue entries, optionally filtered by substring."""
    result = list(_SPECS)
    if market:
        result = [spec for spec in result if market.lower() in spec.market.lower()]
    if transport:
        result = [spec for spec in result if transport.lower() in spec.transport.lower()]
    return result
