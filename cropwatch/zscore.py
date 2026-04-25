"""Z-score normalization and outlier ranking across weeks for a commodity/state."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional


class ZScoreError(Exception):
    """Raised when z-score computation fails."""


@dataclass
class ZScoreResult:
    week_desc: str
    value: float
    zscore: float


def _mean_std(values: List[float]) -> tuple[float, float]:
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return mean, math.sqrt(variance)


def compute_zscores(
    records: List[dict],
    commodity: str,
    attribute: str,
    state: Optional[str] = None,
) -> List[ZScoreResult]:
    """Compute z-scores for each week's value of *attribute* for *commodity*.

    Args:
        records: Raw USDA API records.
        commodity: Commodity description to filter on.
        attribute: Short description (e.g. "PROGRESS, MEASURED IN PCT HARVESTED").
        state: Optional state name to restrict results.

    Returns:
        List of ZScoreResult sorted by descending absolute z-score.

    Raises:
        ZScoreError: If fewer than 2 valid data points are found.
    """
    filtered = [
        r for r in records
        if r.get("commodity_desc", "").upper() == commodity.upper()
        and r.get("short_desc", "").upper() == attribute.upper()
        and (state is None or r.get("state_name", "").upper() == state.upper())
    ]

    parsed: List[tuple[str, float]] = []
    for r in filtered:
        try:
            parsed.append((r.get("week_ending", r.get("reference_period_desc", "")), float(r["Value"])))
        except (KeyError, ValueError, TypeError):
            continue

    if len(parsed) < 2:
        raise ZScoreError(
            f"Need at least 2 data points for z-score; got {len(parsed)}."
        )

    values = [v for _, v in parsed]
    mean, std = _mean_std(values)

    if std == 0.0:
        results = [ZScoreResult(week, val, 0.0) for week, val in parsed]
    else:
        results = [
            ZScoreResult(week, val, (val - mean) / std)
            for week, val in parsed
        ]

    results.sort(key=lambda r: abs(r.zscore), reverse=True)
    return results


def format_zscores(results: List[ZScoreResult], top_n: int = 10) -> str:
    """Format z-score results as a text table."""
    lines = [
        f"{'Week':<14} {'Value':>8} {'Z-Score':>9}",
        "-" * 35,
    ]
    for r in results[:top_n]:
        lines.append(f"{r.week_desc:<14} {r.value:>8.1f} {r.zscore:>+9.3f}")
    return "\n".join(lines)
