"""Dispersion analysis: measure how spread out crop progress values are
across states for a given commodity and week.

Provides inter-quartile range (IQR), range (max-min), and coefficient of
variation (CV = std/mean) so users can quickly see whether states are
clustered together or wildly divergent.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional


class DispersionError(Exception):
    """Raised when dispersion cannot be computed."""


@dataclass
class DispersionResult:
    commodity: str
    week_ending: str
    n: int          # number of state observations
    mean: float
    median: float
    std: float
    minimum: float
    maximum: float
    range_: float   # max - min
    iqr: float      # Q3 - Q1
    cv: float       # coefficient of variation (std / mean), 0 if mean==0


def _percentile(sorted_vals: List[float], pct: float) -> float:
    """Return the *pct*-th percentile of an already-sorted list (0-100 scale)."""
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    idx = (pct / 100.0) * (n - 1)
    lo = int(idx)
    hi = lo + 1
    if hi >= n:
        return sorted_vals[-1]
    frac = idx - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


def compute_dispersion(
    records: List[dict],
    commodity: str,
    week_ending: str,
    state: Optional[str] = None,
) -> DispersionResult:
    """Compute dispersion statistics for *commodity* on *week_ending*.

    Args:
        records:     Raw USDA API records (list of dicts).
        commodity:   Commodity name to filter on (case-insensitive).
        week_ending: The ``week_ending`` date string to analyse.
        state:       Optional state abbreviation to restrict to a subset
                     (rarely useful here but kept for API consistency).

    Returns:
        A :class:`DispersionResult` instance.

    Raises:
        DispersionError: If fewer than two valid observations are found.
    """
    values: List[float] = []
    for rec in records:
        if rec.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if rec.get("week_ending") != week_ending:
            continue
        # Exclude national roll-up rows
        st = rec.get("state_alpha", "").upper()
        if st in ("", "US"):
            continue
        if state and st != state.upper():
            continue
        raw = rec.get("Value")
        try:
            values.append(float(raw))
        except (TypeError, ValueError):
            continue

    if len(values) < 2:
        raise DispersionError(
            f"Need at least 2 state observations for '{commodity}' on "
            f"{week_ending}, found {len(values)}."
        )

    values.sort()
    n = len(values)
    mean = sum(values) / n
    median = _percentile(values, 50)
    variance = sum((v - mean) ** 2 for v in values) / n
    std = math.sqrt(variance)
    minimum = values[0]
    maximum = values[-1]
    range_ = maximum - minimum
    q1 = _percentile(values, 25)
    q3 = _percentile(values, 75)
    iqr = q3 - q1
    cv = (std / mean) if mean != 0 else 0.0

    return DispersionResult(
        commodity=commodity,
        week_ending=week_ending,
        n=n,
        mean=round(mean, 2),
        median=round(median, 2),
        std=round(std, 2),
        minimum=minimum,
        maximum=maximum,
        range_=round(range_, 2),
        iqr=round(iqr, 2),
        cv=round(cv, 4),
    )


def format_dispersion(result: DispersionResult) -> str:
    """Return a human-readable summary of a :class:`DispersionResult`."""
    lines = [
        f"Dispersion — {result.commodity}  |  week ending {result.week_ending}",
        "-" * 52,
        f"  States (n)   : {result.n}",
        f"  Mean         : {result.mean:.2f}%",
        f"  Median       : {result.median:.2f}%",
        f"  Std Dev      : {result.std:.2f}%",
        f"  Min          : {result.minimum:.2f}%",
        f"  Max          : {result.maximum:.2f}%",
        f"  Range        : {result.range_:.2f}%",
        f"  IQR (Q1-Q3)  : {result.iqr:.2f}%",
        f"  CV           : {result.cv:.4f}  ({result.cv * 100:.2f}% of mean)",
    ]
    return "\n".join(lines)
