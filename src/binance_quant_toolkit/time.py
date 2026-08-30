"""UTC and fixed-interval helpers."""

from __future__ import annotations

import pandas as pd

from .exceptions import ValidationError

INTERVALS_MS: dict[str, int] = {
    "1s": 1_000,
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
}

STATISTICS_PERIODS = frozenset({"5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"})


def parse_utc(value: str | pd.Timestamp, *, name: str = "timestamp") -> pd.Timestamp:
    """Parse a date as UTC; naive inputs are deliberately interpreted as UTC."""
    try:
        result = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{name} is not a valid date: {value!r}") from exc
    if result.tzinfo is None:
        result = result.tz_localize("UTC")
    else:
        result = result.tz_convert("UTC")
    return result


def to_milliseconds(value: str | pd.Timestamp) -> int:
    return int(parse_utc(value).timestamp() * 1_000)


def interval_milliseconds(interval: str) -> int:
    try:
        return INTERVALS_MS[interval]
    except KeyError as exc:
        allowed = ", ".join(INTERVALS_MS)
        raise ValidationError(
            f"Unsupported fixed interval {interval!r}. Choose one of: {allowed}"
        ) from exc


def validate_range(
    start: str | pd.Timestamp, end: str | pd.Timestamp
) -> tuple[pd.Timestamp, pd.Timestamp]:
    start_utc = parse_utc(start, name="start")
    end_utc = parse_utc(end, name="end")
    if start_utc >= end_utc:
        raise ValidationError("start must be earlier than end; end is exclusive")
    return start_utc, end_utc
