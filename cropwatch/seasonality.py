"""Seasonality detection: identify which week-of-year typically peaks or troughs."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import mean
from typing import List, Optional


class SeasonalityError(Exception):
    """Raised when seasonality computation fails."""


@dataclass
class SeasonalityResult:
    commodity: str
    state: Optional[str]
    peak_week: int
    peak_avg: float
    trough_week: int
    trough_avg: float
    week_averages: dict  # week_desc -> avg_value


def _extract_week_averages(records: list, commodity: str, state: Optional[str]) -> dict:
    """Return {week_desc: mean_value} across all years for the given filters."""
    buckets: dict = defaultdict(list)
    for rec in records:
        if rec.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if state and rec.get("state_alpha", "").upper() != state.upper():
            continue
        week = rec.get("week_ending") or rec.get("reference_period_desc", "")
        raw = rec.get("Value", "")
        try:
            val = float(str(raw).replace(",", ""))
        except (ValueError, TypeError):
            continue
        if week:
            buckets[week].append(val)
    if not buckets:
        return {}
    return {week: mean(vals) for week, vals in buckets.items()}


def compute_seasonality(
    records: list,
    commodity: str,
    state: Optional[str] = None,
) -> SeasonalityResult:
    """Compute the peak and trough week for a commodity (optionally filtered by state)."""
    if not records:
        raise SeasonalityError("No records provided.")
    week_avgs = _extract_week_averages(records, commodity, state)
    if not week_avgs:
        raise SeasonalityError(
            f"No numeric data found for commodity='{commodity}' state='{state}'."
        )
    peak_week = max(week_avgs, key=lambda w: week_avgs[w])
    trough_week = min(week_avgs, key=lambda w: week_avgs[w])
    return SeasonalityResult(
        commodity=commodity,
        state=state,
        peak_week=peak_week,
        peak_avg=round(week_avgs[peak_week], 2),
        trough_week=trough_week,
        trough_avg=round(week_avgs[trough_week], 2),
        week_averages={w: round(v, 2) for w, v in week_avgs.items()},
    )


def format_seasonality(result: SeasonalityResult) -> str:
    """Render a SeasonalityResult as a human-readable string."""
    state_label = result.state if result.state else "US"
    lines = [
        f"Seasonality — {result.commodity} ({state_label})",
        "-" * 44,
        f"  Peak   week : {result.peak_week:<20} avg={result.peak_avg:.2f}%",
        f"  Trough week : {result.trough_week:<20} avg={result.trough_avg:.2f}%",
        "-" * 44,
        f"  Weeks tracked: {len(result.week_averages)}",
    ]
    return "\n".join(lines)
