"""Deterministic quality checks for canonical kline datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from .exceptions import DataQualityError, ValidationError
from .schemas import KLINE_COLUMNS
from .time import interval_milliseconds, parse_utc


@dataclass(frozen=True)
class QualityReport:
    rows: int
    unique_open_times: int
    duplicate_open_times: int
    missing_bars: int
    invalid_ohlc_rows: int
    negative_volume_rows: int
    negative_trade_count_rows: int
    non_monotonic_rows: int
    first_open_time: str | None
    last_open_time: str | None

    @property
    def passed(self) -> bool:
        return all(
            value == 0
            for value in (
                self.duplicate_open_times,
                self.missing_bars,
                self.invalid_ohlc_rows,
                self.negative_volume_rows,
                self.negative_trade_count_rows,
                self.non_monotonic_rows,
            )
        )

    def to_dict(self) -> dict[str, int | str | bool | None]:
        return {**asdict(self), "passed": self.passed}

    def require_clean(self) -> None:
        if not self.passed:
            problems = [
                f"{key}={value}"
                for key, value in self.to_dict().items()
                if key
                not in {"rows", "unique_open_times", "first_open_time", "last_open_time", "passed"}
                and isinstance(value, int)
                and value > 0
            ]
            raise DataQualityError("kline quality gate failed: " + ", ".join(problems))


def audit_klines(
    frame: pd.DataFrame,
    interval: str,
    *,
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
) -> QualityReport:
    """Audit schema, continuity and elementary exchange invariants."""
    missing_columns = [column for column in KLINE_COLUMNS if column not in frame]
    if missing_columns:
        raise ValidationError(f"missing canonical kline columns: {', '.join(missing_columns)}")
    step = pd.Timedelta(milliseconds=interval_milliseconds(interval))
    if frame.empty:
        expected = 0
        if start is not None and end is not None:
            expected = len(
                pd.date_range(parse_utc(start), parse_utc(end), freq=step, inclusive="left")
            )
        return QualityReport(0, 0, 0, expected, 0, 0, 0, 0, None, None)

    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    duplicate_count = int(times.duplicated().sum())
    non_monotonic = int((times.diff().dropna() <= pd.Timedelta(0)).sum())
    unique_times = pd.DatetimeIndex(times.dropna().drop_duplicates().sort_values())
    if start is not None and end is not None:
        expected_index = pd.date_range(
            parse_utc(start), parse_utc(end), freq=step, inclusive="left"
        )
        missing_bars = len(expected_index.difference(unique_times))
    else:
        expected_index = pd.date_range(unique_times[0], unique_times[-1], freq=step)
        missing_bars = len(expected_index.difference(unique_times))

    numeric = frame[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce")
    maximum_body = numeric[["open", "close"]].max(axis=1)
    minimum_body = numeric[["open", "close"]].min(axis=1)
    invalid_ohlc = (
        numeric.isna().any(axis=1)
        | (numeric <= 0).any(axis=1)
        | (numeric["high"] < maximum_body)
        | (numeric["low"] > minimum_body)
        | (numeric["high"] < numeric["low"])
    )
    volume = pd.to_numeric(frame["volume"], errors="coerce")
    trades = pd.to_numeric(frame["trade_count"], errors="coerce")
    return QualityReport(
        rows=len(frame),
        unique_open_times=len(unique_times),
        duplicate_open_times=duplicate_count,
        missing_bars=int(missing_bars),
        invalid_ohlc_rows=int(invalid_ohlc.sum()),
        negative_volume_rows=int((volume < 0).sum()),
        negative_trade_count_rows=int((trades < 0).sum()),
        non_monotonic_rows=non_monotonic,
        first_open_time=unique_times[0].isoformat(),
        last_open_time=unique_times[-1].isoformat(),
    )
