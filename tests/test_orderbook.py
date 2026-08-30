from decimal import Decimal

import pytest

from binance_quant_toolkit import DataQualityError
from binance_quant_toolkit.orderbook import LocalOrderBook


def test_snapshot_and_depth_events_update_best_prices():
    book = LocalOrderBook()
    book.load_snapshot(100, [["10", "2"]], [["11", "3"]])
    assert book.apply_usdm_event(
        {"U": 99, "u": 101, "pu": 98, "b": [["10", "0"], ["9", "4"]], "a": [["11", "2"]]}
    )
    assert book.best_bid == (Decimal("9"), Decimal("4"))
    assert book.best_ask == (Decimal("11"), Decimal("2"))


def test_sequence_gap_is_fatal():
    book = LocalOrderBook()
    book.load_snapshot(100, [["10", "2"]], [["11", "3"]])
    book.apply_usdm_event({"U": 100, "u": 101, "pu": 99, "b": [], "a": []})
    with pytest.raises(DataQualityError, match="sequence gap"):
        book.apply_usdm_event({"U": 103, "u": 104, "pu": 102, "b": [], "a": []})


def test_crossed_book_is_rejected():
    book = LocalOrderBook()
    book.load_snapshot(100, [["10", "2"]], [["11", "3"]])
    with pytest.raises(DataQualityError, match="crossed"):
        book.apply_usdm_event({"U": 100, "u": 101, "pu": 99, "b": [["12", "1"]], "a": []})
