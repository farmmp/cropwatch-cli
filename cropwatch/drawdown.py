"""Drawdown analysis: detect peak-to-trough declines in crop progress values."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class DrawdownError(Exception):
    """Raised when drawdown computation fails."""


@dataclass
class DrawdownResult:
    commodity: str
    state: str
    peak_week: int
    peak_value: float
    trough_week: int
    trough_value: float
    drawdown: float  # peak_value - trough_value


def _extract_sorted(
    records: List[dict],
    commodity: str,
    state: str,
    attribute: str,
) -> List[tuple[int, float]]:
    """Return (week_ending, value) pairs sorted by week for matching records."""
    series: List[tuple[int, float]] = []
    for r in records:
        if r.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if state and r.get("state_alpha", "").upper() != state.upper():
            continue
        if r.get("statisticcat_desc", "").upper() != attribute.upper():
            continue
        try:
            week = int(r["week_ending"].replace("-", ""))
            value = float(r["Value"])
        except (KeyError, ValueError, TypeError):
            continue
        series.append((week, value))
    series.sort(key=lambda x: x[0])
    return series


def compute_drawdown(
    records: List[dict],
    commodity: str,
    state: str = "US",
    attribute: str = "PROGRESS",
) -> DrawdownResult:
    """Find the maximum peak-to-trough drawdown in the series."""
    if not records:
        raise DrawdownError("No records provided.")

    series = _extract_sorted(records, commodity, state, attribute)
    if len(series) < 2:
        raise DrawdownError(
            f"Not enough data points for {commodity} / {state} / {attribute}."
        )

    max_drawdown = 0.0
    peak_week, peak_val = series[0]
    best: Optional[tuple[int, float, int, float]] = None

    running_peak_week, running_peak_val = series[0]

    for week, val in series[1:]:
        if val > running_peak_val:
            running_peak_week, running_peak_val = week, val
        else:
            dd = running_peak_val - val
            if dd > max_drawdown:
                max_drawdown = dd
                best = (running_peak_week, running_peak_val, week, val)

    if best is None:
        # Series is monotonically increasing — zero drawdown
        best = (series[0][0], series[0][1], series[-1][0], series[-1][1])
        max_drawdown = 0.0

    return DrawdownResult(
        commodity=commodity,
        state=state,
        peak_week=best[0],
        peak_value=best[1],
        trough_week=best[2],
        trough_value=best[3],
        drawdown=max_drawdown,
    )


def format_drawdown(result: DrawdownResult) -> str:
    """Format a DrawdownResult for terminal display."""
    lines = [
        f"Drawdown Analysis — {result.commodity} ({result.state})",
        "-" * 44,
        f"  Peak  : week {result.peak_week}  →  {result.peak_value:.1f}%",
        f"  Trough: week {result.trough_week}  →  {result.trough_value:.1f}%",
        f"  Max Drawdown: {result.drawdown:.1f} pp",
    ]
    return "\n".join(lines)
