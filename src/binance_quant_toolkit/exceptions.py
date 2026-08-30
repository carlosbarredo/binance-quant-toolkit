"""Package-specific exceptions with actionable messages."""


class BinanceQuantError(Exception):
    """Base class for toolkit errors."""


class ValidationError(BinanceQuantError, ValueError):
    """Raised when a request or dataset violates an explicit contract."""


class BinanceApiError(BinanceQuantError):
    """Raised when Binance returns an invalid or unsuccessful response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class DataQualityError(BinanceQuantError):
    """Raised when a strict quality gate rejects a dataset."""


class OptionalDependencyError(BinanceQuantError, ImportError):
    """Raised when an optional feature needs an extra dependency."""
