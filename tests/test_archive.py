import pandas as pd
import pytest

from binance_quant_toolkit import ArchiveRequest
from binance_quant_toolkit.exceptions import ValidationError


def test_monthly_kline_archive_plan_has_stable_paths():
    request = ArchiveRequest(
        "um",
        "klines",
        "btcusdt",
        "2024-01-15",
        "2024-03-01",
        interval="1m",
        frequency="monthly",
    )
    objects = request.objects()
    assert [item.date_token for item in objects] == ["2024-01", "2024-02"]
    assert objects[0].relative_path == (
        "futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip"
    )


def test_daily_only_dataset_rejects_monthly_frequency():
    with pytest.raises(ValidationError, match="daily archives"):
        ArchiveRequest(
            "um", "metrics", "BTCUSDT", "2024-01-01", "2024-01-02", frequency="monthly"
        ).objects()


def test_auto_uses_daily_for_short_window():
    request = ArchiveRequest("spot", "trades", "ETHUSDT", "2024-01-01", "2024-01-03")
    assert len(request.objects()) == 2
    assert request.objects()[0].frequency == "daily"
    assert request.objects()[0].period == pd.Timestamp("2024-01-01T00:00:00Z")
