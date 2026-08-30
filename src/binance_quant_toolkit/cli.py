"""Command-line interface designed for discovery as well as automation."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .analytics import performance_summary
from .archive import ArchiveRequest, BinanceArchiveClient
from .catalog import list_datasets
from .client import BinanceRestClient, KlineRequest
from .exceptions import BinanceQuantError
from .quality import audit_klines
from .storage import load_dataset, save_dataset
from .stream import record_streams


def _json(value: object) -> None:
    print(json.dumps(value, indent=2, default=str))


def _save(frame, args: argparse.Namespace, dataset: str, **metadata: object) -> None:
    path = save_dataset(
        frame,
        args.output,
        metadata={"dataset": dataset, **metadata},
    )
    print(f"saved {len(frame):,} rows to {path}")


def _add_range(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start", required=True, help="UTC start, inclusive")
    parser.add_argument("--end", required=True, help="UTC end, exclusive")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bqt",
        description="Download, record, audit and describe public Binance market data.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    catalog = commands.add_parser("catalog", help="List datasets and their research uses")
    catalog.add_argument("--market")
    catalog.add_argument("--transport")

    demo = commands.add_parser("demo", help="Audit and describe the bundled offline sample")
    demo.add_argument("--input", type=Path)

    klines = commands.add_parser("klines", help="Download complete Spot or USD-M candle ranges")
    klines.add_argument("symbol")
    klines.add_argument("interval")
    klines.add_argument("--market", choices=["spot", "usdm"], default="usdm")
    klines.add_argument(
        "--price-type", choices=["trade", "mark", "index", "premium"], default="trade"
    )
    _add_range(klines)
    klines.add_argument("--output", type=Path, required=True)

    trades = commands.add_parser(
        "agg-trades", help="Download aggregate trades within REST retention"
    )
    trades.add_argument("symbol")
    trades.add_argument("--market", choices=["spot", "usdm"], default="usdm")
    _add_range(trades)
    trades.add_argument("--output", type=Path, required=True)

    funding = commands.add_parser("funding", help="Download realised USD-M funding rates")
    funding.add_argument("symbol")
    _add_range(funding)
    funding.add_argument("--output", type=Path, required=True)

    depth = commands.add_parser("depth", help="Save one Spot or USD-M order-book snapshot")
    depth.add_argument("symbol")
    depth.add_argument("--market", choices=["spot", "usdm"], default="usdm")
    depth.add_argument("--limit", type=int, default=1_000)
    depth.add_argument("--output", type=Path, required=True)

    ticker = commands.add_parser("book-ticker", help="Save current best bid and ask")
    ticker.add_argument("symbol")
    ticker.add_argument("--market", choices=["spot", "usdm"], default="usdm")
    ticker.add_argument("--output", type=Path, required=True)

    recent = commands.add_parser("recent-trades", help="Save recent individual public trades")
    recent.add_argument("symbol")
    recent.add_argument("--market", choices=["spot", "usdm"], default="usdm")
    recent.add_argument("--limit", type=int, default=1_000)
    recent.add_argument("--output", type=Path, required=True)

    interest = commands.add_parser("open-interest", help="Save the current USD-M open interest")
    interest.add_argument("symbol")
    interest.add_argument("--output", type=Path, required=True)

    mark = commands.add_parser("mark-price", help="Save current USD-M mark and index context")
    mark.add_argument("symbol")
    mark.add_argument("--output", type=Path, required=True)

    statistics = commands.add_parser("stats", help="Download retention-limited USD-M statistics")
    statistics.add_argument(
        "dataset",
        choices=[
            "open_interest_history",
            "global_long_short_ratio",
            "top_account_ratio",
            "top_position_ratio",
            "taker_ratio",
        ],
    )
    statistics.add_argument("symbol")
    statistics.add_argument("period")
    statistics.add_argument("--start")
    statistics.add_argument("--end")
    statistics.add_argument("--output", type=Path, required=True)

    basis = commands.add_parser("basis", help="Download retention-limited USD-M basis statistics")
    basis.add_argument("pair")
    basis.add_argument("contract_type")
    basis.add_argument("period")
    basis.add_argument("--start")
    basis.add_argument("--end")
    basis.add_argument("--output", type=Path, required=True)

    plan = commands.add_parser(
        "archive-plan", help="Show public archive objects without downloading"
    )
    _add_archive_arguments(plan, output=False)

    archive = commands.add_parser(
        "archive-download", help="Download checksummed public ZIP archives"
    )
    _add_archive_arguments(archive, output=True)
    archive.add_argument("--no-checksum", action="store_true")
    archive.add_argument("--fail-missing", action="store_true")

    stream = commands.add_parser("stream", help="Record bounded public WebSocket streams as NDJSON")
    stream.add_argument("--market", choices=["spot", "usdm"], required=True)
    stream.add_argument("--streams", nargs="+", required=True)
    stream.add_argument("--output", type=Path, required=True)
    stream.add_argument("--messages", type=int)
    stream.add_argument("--seconds", type=float)

    audit = commands.add_parser("audit", help="Audit a canonical kline CSV or Parquet file")
    audit.add_argument("input", type=Path)
    audit.add_argument("--interval", required=True)
    audit.add_argument("--start")
    audit.add_argument("--end")
    audit.add_argument("--strict", action="store_true")

    describe = commands.add_parser("describe", help="Describe close-to-close behaviour")
    describe.add_argument("input", type=Path)
    describe.add_argument("--interval", required=True)
    return parser


def _add_archive_arguments(parser: argparse.ArgumentParser, *, output: bool) -> None:
    parser.add_argument("dataset")
    parser.add_argument("symbol")
    parser.add_argument("--market", choices=["spot", "um", "cm"], required=True)
    parser.add_argument("--interval")
    parser.add_argument("--frequency", choices=["auto", "daily", "monthly"], default="auto")
    _add_range(parser)
    if output:
        parser.add_argument("--output-dir", type=Path, required=True)


def _archive_request(args: argparse.Namespace) -> ArchiveRequest:
    return ArchiveRequest(
        args.market,
        args.dataset,
        args.symbol,
        args.start,
        args.end,
        interval=args.interval,
        frequency=args.frequency,
    )


def run(args: argparse.Namespace) -> int:
    if args.command == "catalog":
        for spec in list_datasets(market=args.market, transport=args.transport):
            uses = ", ".join(spec.typical_uses)
            print(f"{spec.key:28} {spec.market:10} {spec.transport:24} {spec.description}")
            print(f"  uses: {uses}")
            print(f"  caveat: {spec.caveat}")
        return 0
    if args.command == "demo":
        source = (
            args.input
            or Path(__file__).resolve().parents[2] / "examples/data/btcusdt_1h_sample.csv"
        )
        frame = load_dataset(source)
        _json(
            {
                "quality": audit_klines(frame, "1h").to_dict(),
                "description": performance_summary(frame, "1h"),
            }
        )
        return 0
    if args.command == "klines":
        request = KlineRequest(
            args.symbol, args.interval, args.start, args.end, args.market, args.price_type
        )
        with BinanceRestClient() as client:
            frame = client.fetch_klines(request)
        _save(
            frame,
            args,
            "klines",
            market=request.market,
            symbol=request.symbol,
            interval=request.interval,
            price_type=request.price_type,
            start=request.start,
            end=request.end,
            end_semantics="exclusive",
        )
        return 0
    if args.command == "agg-trades":
        with BinanceRestClient() as client:
            frame = client.fetch_agg_trades(args.market, args.symbol, args.start, args.end)
        _save(frame, args, "agg_trades", market=args.market, symbol=args.symbol.upper())
        return 0
    if args.command == "funding":
        with BinanceRestClient() as client:
            frame = client.fetch_funding_rates(args.symbol, args.start, args.end)
        _save(frame, args, "funding_rate", market="usdm", symbol=args.symbol.upper())
        return 0
    if args.command == "depth":
        with BinanceRestClient() as client:
            frame = client.depth_snapshot(args.market, args.symbol, limit=args.limit)
        _save(frame, args, "depth_snapshot", market=args.market, symbol=args.symbol.upper())
        return 0
    if args.command == "book-ticker":
        with BinanceRestClient() as client:
            frame = client.book_ticker(args.market, args.symbol)
        _save(frame, args, "book_ticker", market=args.market, symbol=args.symbol.upper())
        return 0
    if args.command == "recent-trades":
        with BinanceRestClient() as client:
            frame = client.recent_trades(args.market, args.symbol, limit=args.limit)
        _save(frame, args, "trades", market=args.market, symbol=args.symbol.upper())
        return 0
    if args.command == "open-interest":
        with BinanceRestClient() as client:
            frame = client.open_interest(args.symbol)
        _save(frame, args, "open_interest", market="usdm", symbol=args.symbol.upper())
        return 0
    if args.command == "mark-price":
        with BinanceRestClient() as client:
            frame = client.mark_price(args.symbol)
        _save(frame, args, "mark_price", market="usdm", symbol=args.symbol.upper())
        return 0
    if args.command == "stats":
        with BinanceRestClient() as client:
            frame = client.futures_statistics(
                args.dataset,
                args.symbol,
                args.period,
                start=args.start,
                end=args.end,
            )
        _save(frame, args, args.dataset, market="usdm", symbol=args.symbol.upper())
        return 0
    if args.command == "basis":
        with BinanceRestClient() as client:
            frame = client.futures_basis(
                args.pair,
                args.contract_type,
                args.period,
                start=args.start,
                end=args.end,
            )
        _save(frame, args, "basis", market="usdm", pair=args.pair.upper())
        return 0
    if args.command == "archive-plan":
        for item in _archive_request(args).objects():
            print(item.relative_path)
        return 0
    if args.command == "archive-download":
        with BinanceArchiveClient() as client:
            paths = client.download(
                _archive_request(args),
                args.output_dir,
                verify_checksum=not args.no_checksum,
                skip_missing=not args.fail_missing,
                progress=print,
            )
        print(f"ready: {len(paths)} archive(s)")
        return 0
    if args.command == "stream":
        count = asyncio.run(
            record_streams(
                args.market,
                args.streams,
                args.output,
                max_messages=args.messages,
                max_seconds=args.seconds,
            )
        )
        print(f"recorded {count:,} messages to {args.output}")
        return 0
    if args.command == "audit":
        report = audit_klines(
            load_dataset(args.input),
            args.interval,
            start=args.start,
            end=args.end,
        )
        _json(report.to_dict())
        if args.strict:
            report.require_clean()
        return 0
    if args.command == "describe":
        _json(performance_summary(load_dataset(args.input), args.interval))
        return 0
    raise AssertionError(f"unhandled command {args.command}")


def main(argv: list[str] | None = None) -> int:
    try:
        return run(build_parser().parse_args(argv))
    except (BinanceQuantError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
