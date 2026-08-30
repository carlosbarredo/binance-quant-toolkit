"""Canonical dataset persistence with small provenance sidecars."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .exceptions import OptionalDependencyError, ValidationError


def save_dataset(
    frame: pd.DataFrame,
    path: str | Path,
    *,
    metadata: dict[str, Any] | None = None,
) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    suffix = destination.suffix.lower()
    temporary = destination.with_suffix(destination.suffix + ".part")
    if suffix == ".csv":
        frame.to_csv(temporary, index=False, date_format="%Y-%m-%dT%H:%M:%S.%fZ")
    elif suffix == ".parquet":
        try:
            frame.to_parquet(temporary, index=False)
        except ImportError as exc:
            raise OptionalDependencyError(
                "Install Parquet support: pip install -e .[parquet]"
            ) from exc
    else:
        raise ValidationError("output extension must be .csv or .parquet")
    temporary.replace(destination)
    if metadata is not None:
        sidecar = destination.with_suffix(destination.suffix + ".metadata.json")
        payload = {
            "tool": "qinvia-binance-quant-toolkit",
            "schema_version": 1,
            "rows": len(frame),
            **metadata,
        }
        sidecar.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return destination


def load_dataset(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    if not source.exists():
        raise ValidationError(f"dataset not found: {source}")
    suffix = source.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(source)
    elif suffix == ".parquet":
        try:
            frame = pd.read_parquet(source)
        except ImportError as exc:
            raise OptionalDependencyError(
                "Install Parquet support: pip install -e .[parquet]"
            ) from exc
    else:
        raise ValidationError("dataset extension must be .csv or .parquet")
    for column in frame.columns:
        if column.endswith("_time") or column in {"timestamp", "time"}:
            converted = pd.to_datetime(frame[column], utc=True, errors="coerce")
            if converted.notna().any():
                frame[column] = converted
    return frame
