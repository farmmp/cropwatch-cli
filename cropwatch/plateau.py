"""Plateau detection: find weeks where values stopped changing meaningfully."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class PlateauError(Exception):
    """Raised when plateau detection cannot proceed."""


@dataclass
class PlateauResult:
    commodity: str
    state: Optional[str]
    start_week: int
    end_week: int
    length: int          # number of consecutive weeks in plateau
    avg_value: float


def _extract_sorted(
    records: list,
    commodity: str,
    state: Optional[str],
) -> list[tuple[int, float]]:
    """Return (week_ending, value) pairs sorted by week, filtered by commodity/state."""
    out: list[tuple[int, float]] = []
    for r in records:
        if r.get("commodity_desc", "") != commodity:
            continue
        if state and r.get("state_alpha", "") != state.upper():
            continue
        try:
            week = int(r["week_ending"].replace("-", ""))
            val = float(r["Value"])
        except (KeyError, ValueError, TypeError):
            continue
        out.append((week, val))
    return sorted(out, key=lambda x: x[0])


def detect_plateaus(
    records: list,
    commodity: str,
    state: Optional[str] = None,
    tolerance: float = 1.0,
    min_length: int = 3,
) -> list[PlateauResult]:
    """Detect runs of weeks where the value changes by <= *tolerance*.

    Args:
        records: Raw USDA API records.
        commodity: Crop name to filter on.
        state: Optional two-letter state abbreviation.
        tolerance: Maximum absolute change between consecutive weeks to count
                   as "flat" (default 1.0 percentage point).
        min_length: Minimum number of consecutive flat weeks to report.

    Returns:
        List of PlateauResult, one per detected plateau.

    Raises:
        PlateauError: If no usable data is found.
    """
    series = _extract_sorted(records, commodity, state)
    if not series:
        raise PlateauError(
            f"No data found for commodity='{commodity}' state='{state}'"
        )

    results: list[PlateauResult] = []
    run_start = 0

    for i in range(1, len(series)):
        delta = abs(series[i][1] - series[i - 1][1])
        if delta <= tolerance:
            continue  # still flat — keep extending the run
        # run ended at i-1
        run_len = i - run_start
        if run_len >= min_length:
            weeks = series[run_start:i]
            results.append(
                PlateauResult(
                    commodity=commodity,
                    state=state,
                    start_week=weeks[0][0],
                    end_week=weeks[-1][0],
                    length=run_len,
                    avg_value=sum(v for _, v in weeks) / run_len,
                )
            )
        run_start = i

    # check trailing run
    run_len = len(series) - run_start
    if run_len >= min_length:
        weeks = series[run_start:]
        results.append(
            PlateauResult(
                commodity=commodity,
                state=state,
                start_week=weeks[0][0],
                end_week=weeks[-1][0],
                length=run_len,
                avg_value=sum(v for _, v in weeks) / run_len,
            )
        )

    return results


def format_plateaus(plateaus: list[PlateauResult], commodity: str) -> str:
    """Return a human-readable table of plateau results."""
    if not plateaus:
        return f"No plateaus detected for {commodity}."

    header = f"{'Start':>10}  {'End':>10}  {'Weeks':>5}  {'Avg Value':>10}"
    sep = "-" * len(header)
    lines = [f"Plateaus — {commodity}", sep, header, sep]
    for p in plateaus:
        lines.append(
            f"{str(p.start_week):>10}  {str(p.end_week):>10}"
            f"  {p.length:>5}  {p.avg_value:>9.1f}%"
        )
    lines.append(sep)
    return "\n".join(lines)
