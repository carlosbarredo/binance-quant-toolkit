"""Download a compact USD-M research bundle with one shared UTC window."""

from pathlib import Path

from binance_quant_toolkit import BinanceRestClient, KlineRequest, save_dataset

SYMBOL = "BTCUSDT"
START = "2024-01-01"
END = "2024-01-08"
OUTPUT = Path("data/research_bundle")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with BinanceRestClient() as client:
        for price_type in ("trade", "mark", "index", "premium"):
            request = KlineRequest(SYMBOL, "5m", START, END, "usdm", price_type)
            frame = client.fetch_klines(request)
            save_dataset(
                frame,
                OUTPUT / f"{SYMBOL.lower()}_{price_type}_5m.csv",
                metadata={
                    "dataset": "klines",
                    "market": "usdm",
                    "symbol": SYMBOL,
                    "price_type": price_type,
                    "start": START,
                    "end": END,
                },
            )

        funding = client.fetch_funding_rates(SYMBOL, START, END)
        save_dataset(
            funding,
            OUTPUT / f"{SYMBOL.lower()}_funding.csv",
            metadata={"dataset": "funding_rate", "market": "usdm", "symbol": SYMBOL},
        )

        trades = client.fetch_agg_trades("usdm", SYMBOL, START, END)
        save_dataset(
            trades,
            OUTPUT / f"{SYMBOL.lower()}_agg_trades.csv",
            metadata={"dataset": "agg_trades", "market": "usdm", "symbol": SYMBOL},
        )

        depth = client.depth_snapshot("usdm", SYMBOL, limit=1_000)
        save_dataset(
            depth,
            OUTPUT / f"{SYMBOL.lower()}_depth_snapshot.csv",
            metadata={"dataset": "depth_snapshot", "market": "usdm", "symbol": SYMBOL},
        )


if __name__ == "__main__":
    main()
