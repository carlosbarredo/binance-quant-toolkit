"""Normalisers for Binance public market-data responses."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

import pandas as pd

KLINE_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "ignore",
]

KLINE_NUMERIC = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
]


def empty_klines() -> pd.DataFrame:
    return normalize_klines([])


def normalize_klines(rows: Sequence[Sequence[object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=KLINE_COLUMNS)
    for column in KLINE_NUMERIC:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("float64")
    for column in ("trade_count", "ignore"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")
    for column in ("open_time", "close_time"):
        frame[column] = pd.to_datetime(frame[column], unit="ms", utc=True)
    return frame


def normalize_agg_trades(rows: Iterable[Mapping[str, object]]) -> pd.DataFrame:
    records = []
    for row in rows:
        records.append(
            {
                "aggregate_trade_id": row.get("a"),
                "price": row.get("p"),
                "quantity": row.get("q"),
                "first_trade_id": row.get("f"),
                "last_trade_id": row.get("l"),
                "event_time": row.get("T"),
                "buyer_is_maker": row.get("m"),
            }
        )
    frame = pd.DataFrame.from_records(
        records,
        columns=[
            "aggregate_trade_id",
            "price",
            "quantity",
            "first_trade_id",
            "last_trade_id",
            "event_time",
            "buyer_is_maker",
        ],
    )
    for column in ("aggregate_trade_id", "first_trade_id", "last_trade_id"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")
    for column in ("price", "quantity"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("float64")
    frame["event_time"] = pd.to_datetime(frame["event_time"], unit="ms", utc=True)
    frame["buyer_is_maker"] = frame["buyer_is_maker"].astype("boolean")
    return frame


def normalize_funding(rows: Iterable[Mapping[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame.from_records(rows)
    if frame.empty:
        return pd.DataFrame(
            {
                "symbol": pd.Series(dtype="string"),
                "funding_time": pd.Series(dtype="datetime64[ns, UTC]"),
                "funding_rate": pd.Series(dtype="float64"),
                "mark_price": pd.Series(dtype="float64"),
                "rate_type": pd.Series(dtype="string"),
            }
        )
    frame = frame.rename(
        columns={
            "fundingTime": "funding_time",
            "fundingRate": "funding_rate",
            "markPrice": "mark_price",
            "rateType": "rate_type",
        }
    )
    frame["funding_time"] = pd.to_datetime(frame["funding_time"], unit="ms", utc=True)
    for column in ("funding_rate", "mark_price"):
        if column not in frame:
            frame[column] = pd.NA
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if "rate_type" not in frame:
        frame["rate_type"] = pd.NA
    return frame[["symbol", "funding_time", "funding_rate", "mark_price", "rate_type"]]


def normalize_statistics(rows: Iterable[Mapping[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame.from_records(rows)
    if frame.empty:
        return frame
    for time_column in ("timestamp", "time"):
        if time_column in frame:
            frame[time_column] = pd.to_datetime(frame[time_column], unit="ms", utc=True)
    protected = {"symbol", "pair", "contractType", "timestamp", "time"}
    for column in frame.columns.difference(list(protected)):
        converted = pd.to_numeric(frame[column], errors="coerce")
        if converted.notna().any():
            frame[column] = converted
    return frame


def normalize_depth_snapshot(payload: Mapping[str, object], *, symbol: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for side, key in (("bid", "bids"), ("ask", "asks")):
        for price, quantity in payload.get(key, []):
            rows.append(
                {
                    "symbol": symbol,
                    "side": side,
                    "price": float(price),
                    "quantity": float(quantity),
                    "last_update_id": int(payload["lastUpdateId"]),
                }
            )
    return pd.DataFrame.from_records(
        rows, columns=["symbol", "side", "price", "quantity", "last_update_id"]
    )
