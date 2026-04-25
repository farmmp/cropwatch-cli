"""Detect inflection points (trend reversals) in crop progress time series."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class InflectionError(Exception):
    """Raised when inflection detection fails."""


@dataclass
class InflectionPoint:
    week_ending: str
    value: float
    prior_direction: str   # 'up' or 'down'
    new_direction: str     # 'up' or 'down'


def _extract_sorted(records: list, commodity: str, state: Optional[str]) -> list:
    """Return (week_ending, value) pairs sorted by week for the given filters."""
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
    out.sort(key=lambda x: x[0])
    return out


def detect_inflections(
    records: list,
    commodity: str,
    state: Optional[str] = None,
    min_change: float = 2.0,
) -> List[InflectionPoint]:
    """Detect weeks where the trend direction reverses by at least *min_change*."""
    series = _extract_sorted(records, commodity, state)
    if len(series) < 3:
        raise InflectionError(
            "Need at least 3 data points to detect inflections."
        )

    inflections: List[InflectionPoint] = []
    for i in range(1, len(series) - 1):
        prev_val = series[i - 1][1]
        curr_val = series[i][1]
        next_val = series[i + 1][1]

        delta_before = curr_val - prev_val
        delta_after = next_val - curr_val

        if abs(delta_before) < min_change or abs(delta_after) < min_change:
            continue

        dir_before = "up" if delta_before > 0 else "down"
        dir_after = "up" if delta_after > 0 else "down"

        if dir_before != dir_after:
            inflections.append(
                InflectionPoint(
                    week_ending=series[i][0],
                    value=curr_val,
                    prior_direction=dir_before,
                    new_direction=dir_after,
                )
            )
    return inflections


def format_inflections(inflections: List[InflectionPoint], commodity: str) -> str:
    """Return a human-readable table of inflection points."""
    if not inflections:
        return f"No inflection points found for {commodity}."
    header = f"{'Week':<14} {'Value':>7}  Reversal"
    sep = "-" * 38
    lines = [f"Inflection Points — {commodity}", sep, header, sep]
    for pt in inflections:
        arrow = f"{pt.prior_direction} → {pt.new_direction}"
        lines.append(f"{pt.week_ending:<14} {pt.value:>7.1f}  {arrow}")
    lines.append(sep)
    return "\n".join(lines)
