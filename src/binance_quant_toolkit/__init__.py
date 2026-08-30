"""Public API for Binance Quant Toolkit."""

from .analytics import performance_summary
from .archive import ArchiveRequest, BinanceArchiveClient
from .catalog import DatasetSpec, list_datasets
from .client import BinanceFuturesClient, BinanceRestClient, KlineRequest, RetryPolicy
from .exceptions import BinanceApiError, DataQualityError, ValidationError
from .orderbook import LocalOrderBook
from .quality import QualityReport, audit_klines
from .storage import load_dataset, save_dataset
from .stream import record_streams, validate_streams

__all__ = [
    "ArchiveRequest",
    "BinanceApiError",
    "BinanceArchiveClient",
    "BinanceFuturesClient",
    "BinanceRestClient",
    "DataQualityError",
    "DatasetSpec",
    "KlineRequest",
    "LocalOrderBook",
    "QualityReport",
    "RetryPolicy",
    "ValidationError",
    "audit_klines",
    "list_datasets",
    "load_dataset",
    "performance_summary",
    "record_streams",
    "save_dataset",
    "validate_streams",
]

__version__ = "1.0.0"
