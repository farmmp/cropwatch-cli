"""Streak detection: find consecutive weeks of increase or decrease for a commodity/state."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class StreakError(Exception):
    pass


@dataclass
class StreakResult:
    commodity: str
    state: Optional[str]
    direction: str          # "up" or "down"
    length: int             # number of consecutive weeks
    start_week: int
    end_week: int
    start_value: float
    end_value: float


def _extract_sorted(records: list, commodity: str, state: Optional[str]) -> List[tuple]:
    """Return (week_ending, value) pairs sorted by week for the given filters."""
    out = []
    for r in records:
        if r.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if state and r.get("state_alpha", "").upper() != state.upper():
            continue
        if not state and r.get("state_alpha", "US").upper() != "US":
            continue
        try:
            week = int(r["week_ending"].replace("-", ""))
            value = float(r["Value"])
        except (KeyError, ValueError, TypeError):
            continue
        out.append((week, value))
    out.sort(key=lambda x: x[0])
    return out


def detect_streak(records: list, commodity: str, state: Optional[str] = None) -> StreakResult:
    """Detect the longest consecutive increasing or decreasing streak."""
    if not records:
        raise StreakError("No records provided.")

    series = _extract_sorted(records, commodity, state)
    if len(series) < 2:
        raise StreakError(f"Not enough data points for '{commodity}' to detect a streak.")

    best: Optional[StreakResult] = None
    cur_dir: Optional[str] = None
    cur_start = 0

    for i in range(1, len(series)):
        delta = series[i][1] - series[i - 1][1]
        direction = "up" if delta > 0 else "down" if delta < 0 else None
        if direction is None or direction != cur_dir:
            cur_dir = direction
            cur_start = i - 1
        if direction is not None:
            length = i - cur_start + 1
            if best is None or length > best.length:
                best = StreakResult(
                    commodity=commodity,
                    state=state,
                    direction=direction,
                    length=length,
                    start_week=series[cur_start][0],
                    end_week=series[i][0],
                    start_value=series[cur_start][1],
                    end_value=series[i][1],
                )

    if best is None:
        raise StreakError(f"No directional streak found for '{commodity}'.")
    return best


def format_streak(result: StreakResult) -> str:
    arrow = "▲" if result.direction == "up" else "▼"
    label = result.state if result.state else "US"
    header = f"Longest Streak — {result.commodity} ({label})"
    sep = "─" * len(header)
    return (
        f"{header}\n{sep}\n"
        f"  Direction : {arrow} {result.direction.upper()}\n"
        f"  Length    : {result.length} weeks\n"
        f"  Period    : {result.start_week} → {result.end_week}\n"
        f"  Range     : {result.start_value:.1f}% → {result.end_value:.1f}%\n"
    )
