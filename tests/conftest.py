from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeResponse:
    payload: Any
    status_code: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    text: str = ""
    content: bytes = b""

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.headers = {}
        self.closed = False

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)

    def close(self):
        self.closed = True


def kline(open_time: int, close: str = "101") -> list[object]:
    return [
        open_time,
        "100",
        "102",
        "99",
        close,
        "12.5",
        open_time + 59_999,
        "1260",
        25,
        "6.0",
        "605",
        0,
    ]
