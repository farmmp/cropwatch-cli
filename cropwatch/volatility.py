"""Compute week-over-week volatility (std-dev of changes) for a crop/state series."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class VolatilityError(Exception):
    """Raised when volatility cannot be computed."""


@dataclass
class VolatilityResult:
    commodity: str
    state: Optional[str]
    attribute: str
    mean_change: float
    std_dev: float
    min_change: float
    max_change: float
    weeks: int


def _week_changes(records: list[dict], commodity: str, attribute: str, state: Optional[str]) -> list[float]:
    """Return successive week-over-week numeric differences for the series."""
    filtered = [
        r for r in records
        if r.get("commodity_desc", "").lower() == commodity.lower()
        and r.get("short_desc", "").lower().find(attribute.lower()) != -1
        and (state is None or r.get("state_alpha", "").upper() == state.upper())
    ]
    filtered.sort(key=lambda r: (r.get("year", 0), r.get("week_ending", "")))

    values: list[float] = []
    for r in filtered:
        try:
            values.append(float(r["Value"]))
        except (KeyError, ValueError, TypeError):
            continue

    if len(values) < 2:
        raise VolatilityError(
            f"Need at least 2 data points to compute volatility; got {len(values)}."
        )

    return [values[i + 1] - values[i] for i in range(len(values) - 1)]


def compute_volatility(
    records: list[dict],
    commodity: str,
    attribute: str,
    state: Optional[str] = None,
) -> VolatilityResult:
    """Compute volatility statistics for *commodity* / *attribute* series."""
    changes = _week_changes(records, commodity, attribute, state)
    n = len(changes)
    mean = sum(changes) / n
    variance = sum((c - mean) ** 2 for c in changes) / n
    std_dev = variance ** 0.5
    return VolatilityResult(
        commodity=commodity,
        state=state,
        attribute=attribute,
        mean_change=round(mean, 4),
        std_dev=round(std_dev, 4),
        min_change=round(min(changes), 4),
        max_change=round(max(changes), 4),
        weeks=n + 1,
    )


def format_volatility(result: VolatilityResult) -> str:
    """Return a human-readable summary of the volatility result."""
    scope = result.state if result.state else "US"
    lines = [
        f"Volatility Report — {result.commodity} / {result.attribute} ({scope})",
        "-" * 52,
        f"  Weeks analysed : {result.weeks}",
        f"  Mean Δ/week    : {result.mean_change:+.2f} pp",
        f"  Std-dev        : {result.std_dev:.2f} pp",
        f"  Min Δ          : {result.min_change:+.2f} pp",
        f"  Max Δ          : {result.max_change:+.2f} pp",
    ]
    return "\n".join(lines)
