"""Compute week-over-week acceleration (second derivative) of crop progress values."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class AccelerationError(Exception):
    """Raised when acceleration cannot be computed."""


@dataclass
class AccelerationResult:
    week_ending: str
    value: float
    first_diff: float   # change from previous week
    acceleration: float  # change in first_diff


def _extract_sorted(
    records: List[dict],
    commodity: str,
    state: Optional[str] = None,
) -> List[tuple[str, float]]:
    """Return (week_ending, value) pairs sorted by week_ending."""
    out = []
    for r in records:
        if r.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if state and r.get("state_alpha", "").upper() != state.upper():
            continue
        try:
            val = float(r["Value"])
        except (KeyError, TypeError, ValueError):
            continue
        week = r.get("week_ending", "")
        if week:
            out.append((week, val))
    return sorted(out, key=lambda x: x[0])


def compute_acceleration(
    records: List[dict],
    commodity: str,
    state: Optional[str] = None,
) -> List[AccelerationResult]:
    """Compute acceleration for *commodity* (and optionally *state*).

    Requires at least 3 data points.
    """
    series = _extract_sorted(records, commodity, state)
    if not series:
        raise AccelerationError(f"No data found for commodity '{commodity}'.")
    if len(series) < 3:
        raise AccelerationError(
            f"Need at least 3 data points to compute acceleration; got {len(series)}."
        )

    results = []
    for i in range(2, len(series)):
        week, val = series[i]
        prev_val = series[i - 1][1]
        prev_prev_val = series[i - 2][1]
        first_diff = val - prev_val
        prev_first_diff = prev_val - prev_prev_val
        accel = first_diff - prev_first_diff
        results.append(
            AccelerationResult(
                week_ending=week,
                value=val,
                first_diff=round(first_diff, 4),
                acceleration=round(accel, 4),
            )
        )
    return results


def format_acceleration(results: List[AccelerationResult], commodity: str) -> str:
    """Return a human-readable table of acceleration results."""
    header = f"Acceleration — {commodity}"
    sep = "-" * 56
    col = f"{'Week':<14} {'Value':>7} {'Δ Week':>8} {'Accel':>9}"
    rows = [header, sep, col, sep]
    for r in results:
        rows.append(
            f"{r.week_ending:<14} {r.value:>7.1f} {r.first_diff:>8.2f} {r.acceleration:>9.2f}"
        )
    return "\n".join(rows)
