"""Resilient public REST client for Spot and USD-M futures research data."""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests

from .exceptions import BinanceApiError, ValidationError
from .schemas import (
    normalize_agg_trades,
    normalize_depth_snapshot,
    normalize_funding,
    normalize_klines,
    normalize_statistics,
)
from .time import STATISTICS_PERIODS, interval_milliseconds, parse_utc, validate_range

_SYMBOL = re.compile(r"^[A-Z0-9]{2,30}$")
BASE_URLS = {"spot": "https://api.binance.com", "usdm": "https://fapi.binance.com"}
KLINE_PATHS = {
    ("spot", "trade"): "/api/v3/klines",
    ("usdm", "trade"): "/fapi/v1/klines",
    ("usdm", "mark"): "/fapi/v1/markPriceKlines",
    ("usdm", "index"): "/fapi/v1/indexPriceKlines",
    ("usdm", "premium"): "/fapi/v1/premiumIndexKlines",
}


def _validate_symbol(symbol: str) -> str:
    value = symbol.upper()
    if not _SYMBOL.fullmatch(value):
        raise ValidationError("symbol must contain only 2-30 uppercase letters or digits")
    return value


def _validate_market(market: str) -> str:
    value = market.lower()
    if value not in BASE_URLS:
        raise ValidationError("market must be 'spot' or 'usdm'")
    return value


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 4
    backoff_seconds: float = 0.5
    maximum_backoff_seconds: float = 8.0

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValidationError("retry attempts must be at least one")
        if self.backoff_seconds < 0 or self.maximum_backoff_seconds < 0:
            raise ValidationError("retry delays cannot be negative")


@dataclass(frozen=True)
class KlineRequest:
    symbol: str
    interval: str
    start: str | pd.Timestamp
    end: str | pd.Timestamp
    market: str = "usdm"
    price_type: str = "trade"
    limit: int = 1_000

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _validate_symbol(self.symbol))
        object.__setattr__(self, "market", _validate_market(self.market))
        object.__setattr__(self, "price_type", self.price_type.lower())
        object.__setattr__(self, "start", parse_utc(self.start, name="start"))
        object.__setattr__(self, "end", parse_utc(self.end, name="end"))
        validate_range(self.start, self.end)
        interval_milliseconds(self.interval)
        if self.market == "usdm" and self.interval == "1s":
            raise ValidationError("1s klines are supported for Spot, not USD-M futures")
        if (self.market, self.price_type) not in KLINE_PATHS:
            raise ValidationError(
                f"price_type {self.price_type!r} is not available for {self.market}"
            )
        if not 1 <= self.limit <= 1_000:
            raise ValidationError("limit must be between 1 and 1000")


class BinanceRestClient:
    """Public, read-only client with dependency injection for deterministic tests."""

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        retry: RetryPolicy | None = None,
        timeout: tuple[float, float] = (5.0, 30.0),
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._owns_session = session is None
        self.session = session or requests.Session()
        self.retry = retry or RetryPolicy()
        self.timeout = timeout
        self.sleep = sleep
        self.session.headers.setdefault("User-Agent", "qinvia-binance-quant-toolkit/1.0")

    def __enter__(self) -> BinanceRestClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_session:
            self.session.close()

    def _get(self, market: str, path: str, params: dict[str, Any]) -> Any:
        market = _validate_market(market)
        url = f"{BASE_URLS[market]}{path}"
        last_error: Exception | None = None
        for attempt in range(self.retry.attempts):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code in {418, 429} or response.status_code >= 500:
                    if attempt + 1 < self.retry.attempts:
                        retry_after = response.headers.get("Retry-After")
                        delay = float(retry_after) if retry_after else self._backoff(attempt)
                        self.sleep(min(delay, self.retry.maximum_backoff_seconds))
                        continue
                if not 200 <= response.status_code < 300:
                    raise BinanceApiError(
                        self._error_message(response), status_code=response.status_code
                    )
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise BinanceApiError("Binance returned a non-JSON response") from exc
                if isinstance(payload, dict) and "code" in payload and int(payload["code"]) < 0:
                    raise BinanceApiError(
                        f"Binance error {payload['code']}: {payload.get('msg', 'unknown error')}"
                    )
                return payload
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error = exc
                if attempt + 1 < self.retry.attempts:
                    self.sleep(self._backoff(attempt))
                    continue
        raise BinanceApiError(f"Request failed after {self.retry.attempts} attempts: {last_error}")

    def _backoff(self, attempt: int) -> float:
        return min(self.retry.backoff_seconds * (2**attempt), self.retry.maximum_backoff_seconds)

    @staticmethod
    def _error_message(response: requests.Response) -> str:
        try:
            payload = response.json()
            detail = payload.get("msg") if isinstance(payload, dict) else str(payload)
        except ValueError:
            detail = response.text[:200]
        return f"Binance HTTP {response.status_code}: {detail or 'empty response'}"

    def fetch_klines(self, request: KlineRequest) -> pd.DataFrame:
        """Download every candle in a half-open UTC range."""
        path = KLINE_PATHS[(request.market, request.price_type)]
        step_ms = interval_milliseconds(request.interval)
        cursor = int(request.start.timestamp() * 1_000)
        end_ms = int(request.end.timestamp() * 1_000)
        rows: list[list[object]] = []
        while cursor < end_ms:
            symbol_key = "pair" if request.price_type == "index" else "symbol"
            params = {
                symbol_key: request.symbol,
                "interval": request.interval,
                "startTime": cursor,
                "endTime": end_ms - 1,
                "limit": request.limit,
            }
            page = self._get(request.market, path, params)
            if not isinstance(page, list):
                raise BinanceApiError("Kline response must be a list")
            if not page:
                break
            rows.extend(page)
            last_open = int(page[-1][0])
            next_cursor = last_open + step_ms
            if next_cursor <= cursor:
                raise BinanceApiError("Kline pagination did not advance")
            cursor = next_cursor
            if len(page) < request.limit:
                break
        frame = normalize_klines(rows)
        if frame.empty:
            return frame
        frame = frame[(frame["open_time"] >= request.start) & (frame["open_time"] < request.end)]
        return frame.sort_values("open_time").drop_duplicates("open_time").reset_index(drop=True)

    def fetch_agg_trades(
        self,
        market: str,
        symbol: str,
        start: str | pd.Timestamp,
        end: str | pd.Timestamp,
        *,
        limit: int = 1_000,
    ) -> pd.DataFrame:
        """Download aggregate trades; use archives for ranges outside REST retention."""
        market = _validate_market(market)
        symbol = _validate_symbol(symbol)
        start_utc, end_utc = validate_range(start, end)
        if not 1 <= limit <= 1_000:
            raise ValidationError("limit must be between 1 and 1000")
        path = "/api/v3/aggTrades" if market == "spot" else "/fapi/v1/aggTrades"
        cursor = int(start_utc.timestamp() * 1_000)
        end_ms = int(end_utc.timestamp() * 1_000)
        rows: list[dict[str, object]] = []
        while cursor < end_ms:
            page = self._get(
                market,
                path,
                {"symbol": symbol, "startTime": cursor, "endTime": end_ms - 1, "limit": limit},
            )
            if not isinstance(page, list):
                raise BinanceApiError("Aggregate-trade response must be a list")
            if not page:
                break
            rows.extend(page)
            next_cursor = int(page[-1]["T"]) + 1
            if next_cursor <= cursor:
                raise BinanceApiError("Aggregate-trade pagination did not advance")
            cursor = next_cursor
            if len(page) < limit:
                break
        frame = normalize_agg_trades(rows)
        if frame.empty:
            return frame
        return (
            frame[(frame["event_time"] >= start_utc) & (frame["event_time"] < end_utc)]
            .drop_duplicates("aggregate_trade_id")
            .reset_index(drop=True)
        )

    def fetch_funding_rates(
        self, symbol: str, start: str | pd.Timestamp, end: str | pd.Timestamp, *, limit: int = 1_000
    ) -> pd.DataFrame:
        symbol = _validate_symbol(symbol)
        start_utc, end_utc = validate_range(start, end)
        if not 1 <= limit <= 1_000:
            raise ValidationError("limit must be between 1 and 1000")
        cursor = int(start_utc.timestamp() * 1_000)
        end_ms = int(end_utc.timestamp() * 1_000)
        rows: list[dict[str, object]] = []
        while cursor < end_ms:
            page = self._get(
                "usdm",
                "/fapi/v1/fundingRate",
                {"symbol": symbol, "startTime": cursor, "endTime": end_ms - 1, "limit": limit},
            )
            if not isinstance(page, list):
                raise BinanceApiError("Funding-rate response must be a list")
            if not page:
                break
            rows.extend(page)
            next_cursor = int(page[-1]["fundingTime"]) + 1
            if next_cursor <= cursor:
                raise BinanceApiError("Funding-rate pagination did not advance")
            cursor = next_cursor
            if len(page) < limit:
                break
        frame = normalize_funding(rows)
        if frame.empty:
            return frame
        return (
            frame[(frame["funding_time"] >= start_utc) & (frame["funding_time"] < end_utc)]
            .drop_duplicates(["symbol", "funding_time"])
            .reset_index(drop=True)
        )

    def depth_snapshot(self, market: str, symbol: str, *, limit: int = 1_000) -> pd.DataFrame:
        market = _validate_market(market)
        symbol = _validate_symbol(symbol)
        maximum = 5_000 if market == "spot" else 1_000
        if limit not in {5, 10, 20, 50, 100, 500, 1_000, 5_000} or limit > maximum:
            raise ValidationError(f"invalid depth limit for {market}; maximum is {maximum}")
        path = "/api/v3/depth" if market == "spot" else "/fapi/v1/depth"
        payload = self._get(market, path, {"symbol": symbol, "limit": limit})
        if not isinstance(payload, dict) or "lastUpdateId" not in payload:
            raise BinanceApiError("Depth response has no lastUpdateId")
        return normalize_depth_snapshot(payload, symbol=symbol)

    def book_ticker(self, market: str, symbol: str) -> pd.DataFrame:
        market = _validate_market(market)
        symbol = _validate_symbol(symbol)
        path = "/api/v3/ticker/bookTicker" if market == "spot" else "/fapi/v1/ticker/bookTicker"
        payload = self._get(market, path, {"symbol": symbol})
        frame = pd.DataFrame.from_records([payload])
        for column in ("bidPrice", "bidQty", "askPrice", "askQty"):
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        return frame.rename(
            columns={
                "bidPrice": "bid_price",
                "bidQty": "bid_quantity",
                "askPrice": "ask_price",
                "askQty": "ask_quantity",
            }
        )

    def recent_trades(self, market: str, symbol: str, *, limit: int = 1_000) -> pd.DataFrame:
        """Return recent individual trades; use archives for reproducible history."""
        market = _validate_market(market)
        symbol = _validate_symbol(symbol)
        if not 1 <= limit <= 1_000:
            raise ValidationError("trade limit must be between 1 and 1000")
        path = "/api/v3/trades" if market == "spot" else "/fapi/v1/trades"
        payload = self._get(market, path, {"symbol": symbol, "limit": limit})
        if not isinstance(payload, list):
            raise BinanceApiError("Recent-trades response must be a list")
        return normalize_statistics(payload).rename(
            columns={
                "qty": "quantity",
                "quoteQty": "quote_quantity",
                "isBuyerMaker": "buyer_is_maker",
            }
        )

    def mark_price(self, symbol: str) -> pd.DataFrame:
        """Return the current USD-M mark, index and next-funding context."""
        symbol = _validate_symbol(symbol)
        payload = self._get("usdm", "/fapi/v1/premiumIndex", {"symbol": symbol})
        frame = normalize_statistics([payload]).rename(
            columns={
                "markPrice": "mark_price",
                "indexPrice": "index_price",
                "estimatedSettlePrice": "estimated_settle_price",
                "lastFundingRate": "last_funding_rate",
                "interestRate": "interest_rate",
                "nextFundingTime": "next_funding_time",
            }
        )
        frame["next_funding_time"] = pd.to_datetime(frame["next_funding_time"], unit="ms", utc=True)
        return frame

    def exchange_info(self, market: str) -> dict[str, object]:
        """Return raw public symbol and filter definitions for universe construction."""
        market = _validate_market(market)
        path = "/api/v3/exchangeInfo" if market == "spot" else "/fapi/v1/exchangeInfo"
        payload = self._get(market, path, {})
        if not isinstance(payload, dict) or "symbols" not in payload:
            raise BinanceApiError("Exchange-info response has no symbols")
        return payload

    def open_interest(self, symbol: str) -> pd.DataFrame:
        symbol = _validate_symbol(symbol)
        payload = self._get("usdm", "/fapi/v1/openInterest", {"symbol": symbol})
        return normalize_statistics([payload]).rename(columns={"openInterest": "open_interest"})

    def futures_statistics(
        self,
        dataset: str,
        symbol: str,
        period: str,
        *,
        start: str | pd.Timestamp | None = None,
        end: str | pd.Timestamp | None = None,
        limit: int = 500,
    ) -> pd.DataFrame:
        """Fetch retention-limited USD-M positioning and flow statistics."""
        paths = {
            "open_interest_history": "/futures/data/openInterestHist",
            "global_long_short_ratio": "/futures/data/globalLongShortAccountRatio",
            "top_account_ratio": "/futures/data/topLongShortAccountRatio",
            "top_position_ratio": "/futures/data/topLongShortPositionRatio",
            "taker_ratio": "/futures/data/takerlongshortRatio",
        }
        if dataset not in paths:
            raise ValidationError(f"unknown futures statistics dataset: {dataset}")
        symbol = _validate_symbol(symbol)
        if period not in STATISTICS_PERIODS:
            raise ValidationError("invalid statistics period")
        if not 1 <= limit <= 500:
            raise ValidationError("statistics limit must be between 1 and 500")
        params: dict[str, object] = {"symbol": symbol, "period": period, "limit": limit}
        if (start is None) != (end is None):
            raise ValidationError("provide both start and end, or neither")
        if start is not None and end is not None:
            start_utc, end_utc = validate_range(start, end)
            params.update(
                {
                    "startTime": int(start_utc.timestamp() * 1_000),
                    "endTime": int(end_utc.timestamp() * 1_000) - 1,
                }
            )
        payload = self._get("usdm", paths[dataset], params)
        if not isinstance(payload, list):
            raise BinanceApiError("Statistics response must be a list")
        return normalize_statistics(payload)

    def futures_basis(
        self,
        pair: str,
        contract_type: str,
        period: str,
        *,
        start: str | pd.Timestamp | None = None,
        end: str | pd.Timestamp | None = None,
        limit: int = 500,
    ) -> pd.DataFrame:
        """Fetch retention-limited USD-M basis statistics."""
        pair = _validate_symbol(pair)
        contract_type = contract_type.upper()
        allowed_contracts = {
            "PERPETUAL",
            "CURRENT_MONTH",
            "NEXT_MONTH",
            "CURRENT_QUARTER",
            "NEXT_QUARTER",
        }
        if contract_type not in allowed_contracts:
            raise ValidationError("invalid USD-M contract type")
        if period not in STATISTICS_PERIODS:
            raise ValidationError("invalid basis period")
        if not 1 <= limit <= 500:
            raise ValidationError("basis limit must be between 1 and 500")
        params: dict[str, object] = {
            "pair": pair,
            "contractType": contract_type,
            "period": period,
            "limit": limit,
        }
        if (start is None) != (end is None):
            raise ValidationError("provide both start and end, or neither")
        if start is not None and end is not None:
            start_utc, end_utc = validate_range(start, end)
            params.update(
                {
                    "startTime": int(start_utc.timestamp() * 1_000),
                    "endTime": int(end_utc.timestamp() * 1_000) - 1,
                }
            )
        payload = self._get("usdm", "/futures/data/basis", params)
        if not isinstance(payload, list):
            raise BinanceApiError("Basis response must be a list")
        return normalize_statistics(payload)


class BinanceFuturesClient(BinanceRestClient):
    """Backwards-friendly USD-M client name used by the quickstart."""
