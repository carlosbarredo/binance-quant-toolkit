"""Small, transparent descriptive layer; not a strategy engine."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .exceptions import ValidationError
from .time import interval_milliseconds


def periods_per_year(interval: str) -> float:
    return (365.2425 * 24 * 60 * 60 * 1_000) / interval_milliseconds(interval)


def performance_summary(frame: pd.DataFrame, interval: str) -> dict[str, float | int | None]:
    """Describe close-to-close returns with no transaction-cost claim."""
    if "close" not in frame:
        raise ValidationError("dataset has no close column")
    close = pd.to_numeric(frame["close"], errors="coerce").dropna()
    if len(close) < 2 or (close <= 0).any():
        raise ValidationError("at least two positive close prices are required")
    log_returns = np.log(close).diff().dropna()
    simple_returns = close.pct_change().dropna()
    annual_periods = periods_per_year(interval)
    elapsed_periods = len(close) - 1
    total_return = float(close.iloc[-1] / close.iloc[0] - 1)
    elapsed_days = elapsed_periods * interval_milliseconds(interval) / 86_400_000
    annualized_return = None
    if elapsed_days >= 30:
        annualized_return = float((1 + total_return) ** (annual_periods / elapsed_periods) - 1)
    annualized_volatility = float(log_returns.std(ddof=1) * math.sqrt(annual_periods))
    wealth = (1 + simple_returns).cumprod()
    drawdown = wealth / wealth.cummax() - 1
    return {
        "observations": len(close),
        "elapsed_days": elapsed_days,
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "maximum_drawdown": float(drawdown.min()),
        "positive_return_fraction": float((simple_returns > 0).mean()),
    }
