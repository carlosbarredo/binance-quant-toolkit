"""Bounded WebSocket recorder for public market streams."""

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path

from .exceptions import OptionalDependencyError, ValidationError

STREAM_BASES = {
    "spot": "wss://stream.binance.com:9443/stream",
    "usdm": "wss://fstream.binance.com/public/stream",
}
_STREAM = re.compile(
    r"^[a-z0-9_]{2,40}@(aggTrade|trade|kline_[A-Za-z0-9]+|depth(?:[0-9]+)?(?:@[0-9]+ms)?|bookTicker|markPrice(?:@[0-9]+s)?|forceOrder)$"
)


def validate_streams(market: str, streams: list[str]) -> tuple[str, list[str]]:
    market = market.lower()
    if market not in STREAM_BASES:
        raise ValidationError("stream market must be spot or usdm")
    if not streams:
        raise ValidationError("at least one stream is required")
    if len(streams) > 100:
        raise ValidationError("record at most 100 streams per process")
    normalized = [stream.strip() for stream in streams]
    invalid = [stream for stream in normalized if not _STREAM.fullmatch(stream)]
    if invalid:
        raise ValidationError(f"invalid public stream name: {invalid[0]!r}")
    return market, normalized


async def record_streams(
    market: str,
    streams: list[str],
    output: str | Path,
    *,
    max_messages: int | None = None,
    max_seconds: float | None = None,
) -> int:
    """Record combined stream payloads as append-friendly NDJSON."""
    market, streams = validate_streams(market, streams)
    if max_messages is not None and max_messages < 1:
        raise ValidationError("max_messages must be positive")
    if max_seconds is not None and max_seconds <= 0:
        raise ValidationError("max_seconds must be positive")
    if max_messages is None and max_seconds is None:
        raise ValidationError("set max_messages or max_seconds to keep captures bounded")
    try:
        import websockets
    except ImportError as exc:
        raise OptionalDependencyError("Install the stream extra: pip install -e .[stream]") from exc

    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = f"{STREAM_BASES[market]}?streams={'/'.join(streams)}"
    started = asyncio.get_running_loop().time()
    count = 0
    async with websockets.connect(
        url, ping_interval=20, ping_timeout=20, max_size=8_388_608
    ) as socket:
        with destination.open("a", encoding="utf-8", newline="\n") as handle:
            while True:
                if max_messages is not None and count >= max_messages:
                    break
                elapsed = asyncio.get_running_loop().time() - started
                if max_seconds is not None and elapsed >= max_seconds:
                    break
                remaining = None if max_seconds is None else max_seconds - elapsed
                try:
                    message = await asyncio.wait_for(socket.recv(), timeout=remaining)
                except asyncio.TimeoutError:
                    break
                payload = json.loads(message)
                record = {
                    "received_at_ns": time.time_ns(),
                    "market": market,
                    "payload": payload,
                }
                handle.write(json.dumps(record, separators=(",", ":")) + "\n")
                count += 1
    return count
