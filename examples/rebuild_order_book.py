"""Small sequence-checking example. Values are synthetic."""

from binance_quant_toolkit.orderbook import LocalOrderBook

book = LocalOrderBook()
book.load_snapshot(
    100,
    bids=[["42000.0", "1.2"], ["41999.0", "2.0"]],
    asks=[["42001.0", "0.8"], ["42002.0", "1.5"]],
)

book.apply_usdm_event(
    {
        "U": 99,
        "u": 101,
        "pu": 98,
        "b": [["42000.0", "1.0"]],
        "a": [["42001.0", "0.0"], ["42001.5", "0.7"]],
    }
)

print("best bid:", book.best_bid)
print("best ask:", book.best_ask)
