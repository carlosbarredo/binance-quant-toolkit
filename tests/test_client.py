import pandas as pd
import pytest
from conftest import FakeResponse, FakeSession, kline

from binance_quant_toolkit import BinanceApiError, BinanceRestClient, KlineRequest, RetryPolicy
from binance_quant_toolkit.exceptions import ValidationError


def test_request_parses_naive_dates_as_utc():
    request = KlineRequest("btcusdt", "1m", "2024-01-01", "2024-01-02")
    assert request.symbol == "BTCUSDT"
    assert str(request.start.tz) == "UTC"
    assert request.end == pd.Timestamp("2024-01-02T00:00:00Z")


def test_invalid_range_is_rejected():
    with pytest.raises(ValidationError, match="start must be earlier"):
        KlineRequest("BTCUSDT", "1m", "2024-01-02", "2024-01-01")


def test_one_second_futures_klines_are_rejected():
    with pytest.raises(ValidationError, match="Spot"):
        KlineRequest("BTCUSDT", "1s", "2024-01-01", "2024-01-02", market="usdm")


def test_kline_pagination_advances_and_deduplicates():
    start = pd.Timestamp("2024-01-01T00:00:00Z")
    base = int(start.timestamp() * 1_000)
    session = FakeSession(
        [
            FakeResponse([kline(base), kline(base + 60_000)]),
            FakeResponse([kline(base + 60_000), kline(base + 120_000, "103")]),
        ]
    )
    client = BinanceRestClient(session=session)
    request = KlineRequest("BTCUSDT", "1m", start, start + pd.Timedelta(minutes=3), limit=2)

    result = client.fetch_klines(request)

    assert len(result) == 3
    assert result["open_time"].is_monotonic_increasing
    assert result["open_time"].is_unique
    assert session.calls[1][1]["params"]["startTime"] == base + 120_000


def test_transient_status_is_retried_without_real_sleep():
    session = FakeSession(
        [
            FakeResponse({"msg": "busy"}, status_code=500),
            FakeResponse({"symbol": "BTCUSDT", "openInterest": "42", "time": 1_700_000_000_000}),
        ]
    )
    delays = []
    client = BinanceRestClient(
        session=session,
        retry=RetryPolicy(attempts=2, backoff_seconds=0.25),
        sleep=delays.append,
    )

    result = client.open_interest("BTCUSDT")

    assert len(result) == 1
    assert delays == [0.25]


def test_non_retryable_error_contains_status():
    session = FakeSession([FakeResponse({"msg": "bad symbol"}, status_code=400)])
    client = BinanceRestClient(session=session)
    with pytest.raises(BinanceApiError, match="HTTP 400") as error:
        client.open_interest("BTCUSDT")
    assert error.value.status_code == 400


def test_funding_pagination_is_half_open():
    start = pd.Timestamp("2024-01-01T00:00:00Z")
    base = int(start.timestamp() * 1_000)
    rows = [
        {"symbol": "BTCUSDT", "fundingTime": base, "fundingRate": "0.0001", "markPrice": "42000"},
        {
            "symbol": "BTCUSDT",
            "fundingTime": base + 28_800_000,
            "fundingRate": "0.0002",
            "markPrice": "42100",
        },
    ]
    session = FakeSession([FakeResponse(rows)])
    client = BinanceRestClient(session=session)
    result = client.fetch_funding_rates("BTCUSDT", start, start + pd.Timedelta(hours=9), limit=100)
    assert list(result["funding_rate"]) == [0.0001, 0.0002]
    assert str(result["funding_time"].dt.tz) == "UTC"


def test_mark_price_normalises_next_funding_time():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "symbol": "BTCUSDT",
                    "markPrice": "42000",
                    "indexPrice": "41990",
                    "lastFundingRate": "0.0001",
                    "nextFundingTime": 1_704_096_000_000,
                    "time": 1_704_067_200_000,
                }
            )
        ]
    )
    result = BinanceRestClient(session=session).mark_price("BTCUSDT")
    assert result.loc[0, "mark_price"] == 42000
    assert str(result["next_funding_time"].dt.tz) == "UTC"


def test_basis_uses_pair_and_contract_type():
    session = FakeSession([FakeResponse([])])
    client = BinanceRestClient(session=session)
    result = client.futures_basis("btcusdt", "perpetual", "5m")
    params = session.calls[0][1]["params"]
    assert result.empty
    assert params["pair"] == "BTCUSDT"
    assert params["contractType"] == "PERPETUAL"
