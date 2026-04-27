"""Tapering detection: identifies when a crop progress metric is decelerating
toward a stable end-of-season value (approaching 0 or 100)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class TaperingError(Exception):
    """Raised when tapering detection cannot proceed."""


@dataclass
class TaperingResult:
    commodity: str
    state: str
    week_start: int
    week_end: int
    start_value: float
    end_value: float
    target: float          # 0.0 or 100.0
    avg_weekly_change: float


def _extract_sorted(
    records: list,
    commodity: str,
    state: str = "US",
) -> List[tuple]:
    """Return (week_ending, value) tuples sorted by week, filtered by commodity/state."""
    out = []
    for r in records:
        if r.get("commodity_desc", "").upper() != commodity.upper():
            continue
        if r.get("state_alpha", "US").upper() != state.upper():
            continue
        try:
            week = int(r["week_ending"].replace("-", ""))
            val = float(r["Value"])
        except (KeyError, ValueError, TypeError):
            continue
        out.append((week, val))
    out.sort(key=lambda x: x[0])
    return out


def detect_tapering(
    records: list,
    commodity: str,
    state: str = "US",
    window: int = 4,
    threshold: float = 5.0,
) -> Optional[TaperingResult]:
    """Detect a tapering window in the most recent *window* data points.

    Tapering is defined as all week-over-week changes moving toward 0 or 100
    and each change being smaller in magnitude than the previous one.
    Returns None if no tapering is detected.
    """
    series = _extract_sorted(records, commodity, state)
    if len(series) < 2:
        raise TaperingError(
            f"Not enough data for tapering detection (need ≥2 points, got {len(series)})"
        )

    tail = series[-window:] if len(series) >= window else series
    if len(tail) < 2:
        raise TaperingError("Window too small after filtering.")

    values = [v for _, v in tail]
    changes = [values[i + 1] - values[i] for i in range(len(values) - 1)]

    last_val = values[-1]
    target = 100.0 if last_val >= 50.0 else 0.0

    # All changes must move toward target and be within threshold
    toward = all(
        (c > 0 and target == 100.0) or (c < 0 and target == 0.0)
        for c in changes
    )
    decelerating = all(
        abs(changes[i + 1]) < abs(changes[i]) for i in range(len(changes) - 1)
    )
    small_enough = abs(changes[-1]) <= threshold

    if not (toward and decelerating and small_enough):
        return None

    avg_change = sum(abs(c) for c in changes) / len(changes)
    return TaperingResult(
        commodity=commodity,
        state=state,
        week_start=tail[0][0],
        week_end=tail[-1][0],
        start_value=values[0],
        end_value=last_val,
        target=target,
        avg_weekly_change=round(avg_change, 2),
    )


def format_tapering(result: Optional[TaperingResult], commodity: str, state: str) -> str:
    """Return a human-readable tapering report."""
    if result is None:
        return f"No tapering detected for {commodity} in {state}."
    direction = "ceiling (100%)" if result.target == 100.0 else "floor (0%)"
    lines = [
        f"Tapering Detected — {result.commodity} [{result.state}]",
        f"  Period  : week {result.week_start} → {result.week_end}",
        f"  Range   : {result.start_value:.1f}% → {result.end_value:.1f}%",
        f"  Target  : {direction}",
        f"  Avg Δ/wk: {result.avg_weekly_change:.2f}%",
    ]
    return "\n".join(lines)
