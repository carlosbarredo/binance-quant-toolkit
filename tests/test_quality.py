import pandas as pd
import pytest
from conftest import kline

from binance_quant_toolkit import DataQualityError, audit_klines
from binance_quant_toolkit.schemas import normalize_klines


def test_clean_kline_report_passes():
    base = 1_704_067_200_000
    frame = normalize_klines([kline(base), kline(base + 60_000), kline(base + 120_000)])
    report = audit_klines(frame, "1m")
    assert report.passed
    assert report.missing_bars == 0


def test_gap_and_invalid_ohlc_are_reported():
    base = 1_704_067_200_000
    rows = [kline(base), kline(base + 120_000)]
    rows[1][2] = "98"
    frame = normalize_klines(rows)
    report = audit_klines(frame, "1m")
    assert report.missing_bars == 1
    assert report.invalid_ohlc_rows == 1
    with pytest.raises(DataQualityError, match="missing_bars=1"):
        report.require_clean()


def test_explicit_range_counts_edge_gaps():
    start = pd.Timestamp("2024-01-01T00:00:00Z")
    base = int(start.timestamp() * 1_000)
    frame = normalize_klines([kline(base + 60_000)])
    report = audit_klines(frame, "1m", start=start, end=start + pd.Timedelta(minutes=3))
    assert report.missing_bars == 2
