"""Minimal local order-book state with explicit sequence checks."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal

from .exceptions import DataQualityError, ValidationError


@dataclass
class LocalOrderBook:
    """Apply USD-M depth deltas after bootstrapping from a REST snapshot.

    Buffer WebSocket events first. Fetch the snapshot. Discard events whose
    final update ID is older than the snapshot. The first accepted event must
    bridge the snapshot ID. Later events must name the previous final ID.
    """

    bids: dict[Decimal, Decimal] = field(default_factory=dict)
    asks: dict[Decimal, Decimal] = field(default_factory=dict)
    last_update_id: int | None = None
    _started: bool = False

    def load_snapshot(
        self,
        last_update_id: int,
        bids: Iterable[Iterable[str]],
        asks: Iterable[Iterable[str]],
    ) -> None:
        if last_update_id < 0:
            raise ValidationError("last_update_id cannot be negative")
        self.bids = self._levels(bids)
        self.asks = self._levels(asks)
        self.last_update_id = last_update_id
        self._started = False

    def apply_usdm_event(self, event: dict[str, object]) -> bool:
        if self.last_update_id is None:
            raise ValidationError("load a REST snapshot before applying events")
        first_id = int(event["U"])
        final_id = int(event["u"])
        previous_id = int(event.get("pu", -1))
        if final_id < self.last_update_id:
            return False
        if not self._started:
            if not first_id <= self.last_update_id <= final_id:
                raise DataQualityError("first depth event does not bridge the snapshot update ID")
            self._started = True
        elif previous_id != self.last_update_id:
            raise DataQualityError(
                f"depth sequence gap: event pu={previous_id}, local u={self.last_update_id}"
            )
        self._apply(self.bids, event.get("b", []))
        self._apply(self.asks, event.get("a", []))
        self.last_update_id = final_id
        if self.bids and self.asks and max(self.bids) >= min(self.asks):
            raise DataQualityError("crossed local order book after applying a depth event")
        return True

    @property
    def best_bid(self) -> tuple[Decimal, Decimal] | None:
        if not self.bids:
            return None
        price = max(self.bids)
        return price, self.bids[price]

    @property
    def best_ask(self) -> tuple[Decimal, Decimal] | None:
        if not self.asks:
            return None
        price = min(self.asks)
        return price, self.asks[price]

    @staticmethod
    def _levels(rows: Iterable[Iterable[str]]) -> dict[Decimal, Decimal]:
        result: dict[Decimal, Decimal] = {}
        LocalOrderBook._apply(result, rows)
        return result

    @staticmethod
    def _apply(book: dict[Decimal, Decimal], rows: Iterable[Iterable[str]]) -> None:
        for row in rows:
            price_text, quantity_text = row
            price = Decimal(price_text)
            quantity = Decimal(quantity_text)
            if price <= 0 or quantity < 0:
                raise DataQualityError(
                    "order-book prices must be positive and quantities non-negative"
                )
            if quantity == 0:
                book.pop(price, None)
            else:
                book[price] = quantity
