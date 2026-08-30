import json

import pandas as pd
import pytest

from binance_quant_toolkit import load_dataset, performance_summary, save_dataset


def test_csv_round_trip_and_metadata(tmp_path):
    frame = pd.DataFrame(
        {
            "open_time": pd.date_range("2024-01-01", periods=2, freq="h", tz="UTC"),
            "close": [100.0, 101.0],
        }
    )
    path = save_dataset(frame, tmp_path / "sample.csv", metadata={"dataset": "test"})
    loaded = load_dataset(path)
    metadata = json.loads((tmp_path / "sample.csv.metadata.json").read_text())
    assert loaded["open_time"].dt.tz is not None
    assert metadata["rows"] == 2
    assert metadata["dataset"] == "test"


def test_performance_summary_is_transparent():
    frame = pd.DataFrame({"close": [100.0, 110.0, 99.0]})
    result = performance_summary(frame, "1d")
    assert result["observations"] == 3
    assert result["total_return"] == pytest.approx(-0.01)
    assert result["maximum_drawdown"] == pytest.approx(-0.10)
