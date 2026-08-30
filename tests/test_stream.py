import pytest

from binance_quant_toolkit import validate_streams
from binance_quant_toolkit.exceptions import ValidationError


def test_public_stream_names_are_normalised():
    market, streams = validate_streams(
        "USDM", ["btcusdt@aggTrade", "btcusdt@depth@100ms", "btcusdt@forceOrder"]
    )
    assert market == "usdm"
    assert len(streams) == 3


def test_arbitrary_stream_text_is_rejected():
    with pytest.raises(ValidationError, match="invalid public stream"):
        validate_streams("spot", ["https://example.invalid"])
