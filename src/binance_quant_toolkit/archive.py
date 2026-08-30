"""Planner and downloader for Binance's public ZIP archives."""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

from .exceptions import BinanceApiError, DataQualityError, ValidationError
from .time import validate_range

ARCHIVE_ROOT = "https://data.binance.vision/data"
_SYMBOL = re.compile(r"^[A-Z0-9]{2,30}$")
_DATASET = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
_INTERVAL_DATASETS = frozenset(
    {"klines", "markPriceKlines", "indexPriceKlines", "premiumIndexKlines"}
)
_DAILY_ONLY = frozenset({"bookDepth", "bookTicker", "liquidationSnapshot", "metrics"})
_MONTHLY_ONLY = frozenset({"fundingRate"})
_ALLOWED_DATASETS = {
    "spot": frozenset({"klines", "trades", "aggTrades"}),
    "um": frozenset(
        {
            "klines",
            "trades",
            "aggTrades",
            "markPriceKlines",
            "indexPriceKlines",
            "premiumIndexKlines",
            "bookDepth",
            "bookTicker",
            "fundingRate",
            "liquidationSnapshot",
            "metrics",
        }
    ),
    "cm": frozenset(
        {
            "klines",
            "trades",
            "aggTrades",
            "markPriceKlines",
            "indexPriceKlines",
            "premiumIndexKlines",
            "bookDepth",
            "bookTicker",
            "fundingRate",
            "liquidationSnapshot",
            "metrics",
        }
    ),
}


@dataclass(frozen=True)
class ArchiveRequest:
    market: str
    dataset: str
    symbol: str
    start: str | pd.Timestamp
    end: str | pd.Timestamp
    interval: str | None = None
    frequency: str = "auto"

    def __post_init__(self) -> None:
        market = self.market.lower()
        if market not in {"spot", "um", "cm"}:
            raise ValidationError("archive market must be spot, um, or cm")
        symbol = self.symbol.upper()
        if not _SYMBOL.fullmatch(symbol):
            raise ValidationError("invalid archive symbol")
        if not _DATASET.fullmatch(self.dataset):
            raise ValidationError("invalid archive dataset")
        if self.dataset not in _ALLOWED_DATASETS[market]:
            allowed = ", ".join(sorted(_ALLOWED_DATASETS[market]))
            raise ValidationError(
                f"{self.dataset} is not catalogued for {market}; choose: {allowed}"
            )
        start, end = validate_range(self.start, self.end)
        if self.dataset in _INTERVAL_DATASETS and not self.interval:
            raise ValidationError(f"{self.dataset} requires an interval")
        if self.dataset not in _INTERVAL_DATASETS and self.interval:
            raise ValidationError(f"{self.dataset} does not use an interval path")
        if self.frequency not in {"auto", "daily", "monthly"}:
            raise ValidationError("frequency must be auto, daily, or monthly")
        object.__setattr__(self, "market", market)
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)

    def objects(self) -> list[ArchiveObject]:
        frequency = self._resolved_frequency()
        periods = _period_starts(self.start, self.end, frequency)
        return [ArchiveObject(self, frequency, period) for period in periods]

    def _resolved_frequency(self) -> str:
        if self.dataset in _DAILY_ONLY:
            if self.frequency == "monthly":
                raise ValidationError(f"{self.dataset} is available as daily archives")
            return "daily"
        if self.dataset in _MONTHLY_ONLY:
            if self.frequency == "daily":
                raise ValidationError(f"{self.dataset} is available as monthly archives")
            return "monthly"
        if self.frequency != "auto":
            return self.frequency
        span = self.end - self.start
        return "monthly" if span >= pd.Timedelta(days=62) else "daily"


@dataclass(frozen=True)
class ArchiveObject:
    request: ArchiveRequest
    frequency: str
    period: pd.Timestamp

    @property
    def date_token(self) -> str:
        return self.period.strftime("%Y-%m" if self.frequency == "monthly" else "%Y-%m-%d")

    @property
    def filename(self) -> str:
        if self.request.interval:
            return f"{self.request.symbol}-{self.request.interval}-{self.date_token}.zip"
        return f"{self.request.symbol}-{self.request.dataset}-{self.date_token}.zip"

    @property
    def relative_path(self) -> str:
        market_path = "spot" if self.request.market == "spot" else f"futures/{self.request.market}"
        parts = [market_path, self.frequency, self.request.dataset, self.request.symbol]
        if self.request.interval:
            parts.append(self.request.interval)
        parts.append(self.filename)
        return "/".join(parts)

    @property
    def url(self) -> str:
        return f"{ARCHIVE_ROOT}/{self.relative_path}"


def _period_starts(start: pd.Timestamp, end: pd.Timestamp, frequency: str) -> list[pd.Timestamp]:
    end_inclusive = end - pd.Timedelta(nanoseconds=1)
    if frequency == "daily":
        return list(pd.date_range(start.normalize(), end_inclusive.normalize(), freq="D", tz="UTC"))
    first = pd.Timestamp(year=start.year, month=start.month, day=1, tz="UTC")
    last = pd.Timestamp(year=end_inclusive.year, month=end_inclusive.month, day=1, tz="UTC")
    return list(pd.date_range(first, last, freq="MS", tz="UTC"))


class BinanceArchiveClient:
    """Download selected public archive objects with optional SHA-256 verification."""

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        timeout: tuple[float, float] = (5.0, 120.0),
    ) -> None:
        self._owns_session = session is None
        self.session = session or requests.Session()
        self.timeout = timeout
        self.session.headers.setdefault("User-Agent", "qinvia-binance-quant-toolkit/1.0")

    def __enter__(self) -> BinanceArchiveClient:
        return self

    def __exit__(self, *_: object) -> None:
        if self._owns_session:
            self.session.close()

    def download(
        self,
        request: ArchiveRequest,
        output_dir: str | Path,
        *,
        verify_checksum: bool = True,
        skip_missing: bool = True,
        progress: Callable[[str], None] | None = None,
    ) -> list[Path]:
        """Download ZIPs without extracting them; existing valid files are reused."""
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        downloaded: list[Path] = []
        for item in request.objects():
            destination = target / item.filename
            if destination.exists() and destination.stat().st_size > 0:
                downloaded.append(destination)
                if progress:
                    progress(f"reuse {item.filename}")
                continue
            response = self.session.get(item.url, timeout=self.timeout)
            if response.status_code == 404 and skip_missing:
                if progress:
                    progress(f"missing {item.filename}")
                continue
            if not 200 <= response.status_code < 300:
                raise BinanceApiError(
                    f"Archive HTTP {response.status_code} for {item.relative_path}",
                    status_code=response.status_code,
                )
            content = response.content
            if not zipfile.is_zipfile(io.BytesIO(content)):
                raise DataQualityError(f"Downloaded object is not a valid ZIP: {item.filename}")
            if verify_checksum:
                self._verify(item, content)
            temporary = destination.with_suffix(destination.suffix + ".part")
            temporary.write_bytes(content)
            temporary.replace(destination)
            downloaded.append(destination)
            if progress:
                progress(f"downloaded {item.filename}")
        return downloaded

    def _verify(self, item: ArchiveObject, content: bytes) -> None:
        response = self.session.get(f"{item.url}.CHECKSUM", timeout=self.timeout)
        if response.status_code == 404:
            raise DataQualityError(f"Checksum is unavailable for {item.filename}")
        if not 200 <= response.status_code < 300:
            raise BinanceApiError(
                f"Checksum HTTP {response.status_code} for {item.relative_path}",
                status_code=response.status_code,
            )
        expected = response.text.strip().split()[0].lower()
        actual = hashlib.sha256(content).hexdigest()
        if actual != expected:
            raise DataQualityError(f"SHA-256 mismatch for {item.filename}")

    @staticmethod
    def extract(zip_path: str | Path, output_dir: str | Path) -> list[Path]:
        """Safely extract regular files, discarding any archive path components."""
        source = Path(zip_path)
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        extracted: list[Path] = []
        with zipfile.ZipFile(source) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                safe_name = Path(member.filename).name
                if not safe_name:
                    continue
                destination = target / safe_name
                destination.write_bytes(archive.read(member))
                extracted.append(destination)
        return extracted
