"""Momentum analysis: rate-of-change between consecutive weeks for a crop metric."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class MomentumError(Exception):
    """Raised when momentum computation fails."""


@dataclass
class MomentumResult:
    week_ending: str
    value: float
    change: float          # absolute change from prior week
    pct_change: float      # percent change from prior week (0‒100 scale)


def compute_momentum(
    records: List[dict],
    commodity: str,
    attribute: str,
    state: Optional[str] = None,
) -> List[MomentumResult]:
    """Compute week-over-week momentum for *commodity*/*attribute*.

    Parameters
    ----------
    records:   Raw USDA API records.
    commodity: Commodity name filter (case-insensitive).
    attribute: Attribute/description filter (case-insensitive).
    state:     Optional state abbreviation filter.

    Returns a list of MomentumResult sorted by week_ending (ascending).
    At least two data points are required.
    """
    if not records:
        raise MomentumError("No records provided.")

    filtered = [
        r for r in records
        if r.get("commodity_desc", "").lower() == commodity.lower()
        and r.get("short_desc", "").lower().find(attribute.lower()) != -1
        and (state is None or r.get("state_alpha", "").upper() == state.upper())
    ]

    if not filtered:
        raise MomentumError(
            f"No records found for commodity='{commodity}' attribute='{attribute}'."
        )

    # Parse and sort by week_ending
    parsed: list[tuple[str, float]] = []
    for r in filtered:
        raw = r.get("Value", "")
        try:
            parsed.append((r["week_ending"], float(raw)))
        except (ValueError, KeyError):
            continue

    if len(parsed) < 2:
        raise MomentumError("Need at least two numeric data points to compute momentum.")

    parsed.sort(key=lambda t: t[0])

    results: list[MomentumResult] = []
    for i in range(1, len(parsed)):
        prev_val = parsed[i - 1][1]
        curr_val = parsed[i][1]
        change = curr_val - prev_val
        pct = (change / prev_val * 100.0) if prev_val != 0.0 else 0.0
        results.append(
            MomentumResult(
                week_ending=parsed[i][0],
                value=curr_val,
                change=round(change, 2),
                pct_change=round(pct, 2),
            )
        )
    return results


def format_momentum(results: List[MomentumResult], commodity: str, attribute: str) -> str:
    """Return a human-readable table of momentum results."""
    header = f"Momentum — {commodity.title()} / {attribute.title()}"
    sep = "-" * 56
    lines = [header, sep, f"{'Week Ending':<14} {'Value':>8} {'Change':>8} {'% Change':>10}", sep]
    for r in results:
        sign = "+" if r.change >= 0 else ""
        lines.append(
            f"{r.week_ending:<14} {r.value:>8.1f} {sign}{r.change:>7.2f} {sign}{r.pct_change:>9.2f}%"
        )
    lines.append(sep)
    return "\n".join(lines)
