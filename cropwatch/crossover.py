"""Detect crossover events where a short-term moving average crosses a long-term one."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


class CrossoverError(Exception):
    """Raised when crossover detection fails."""


@dataclass
class CrossoverEvent:
    week_ending: str
    direction: str  # "bullish" (short crosses above long) or "bearish"
    short_avg: float
    long_avg: float


def _rolling_mean(values: List[float], window: int) -> List[float | None]:
    """Return a list of rolling means; leading entries are None until window is filled."""
    result: List[float | None] = []
    for i, _ in enumerate(values):
        if i + 1 < window:
            result.append(None)
        else:
            chunk = values[i + 1 - window : i + 1]
            result.append(sum(chunk) / window)
    return result


def detect_crossovers(
    records: list,
    commodity: str,
    short_window: int = 3,
    long_window: int = 6,
    state: str | None = None,
) -> List[CrossoverEvent]:
    """Detect moving-average crossover events in *records* for *commodity*.

    Args:
        records: Raw USDA API records.
        commodity: Commodity description to filter on.
        short_window: Period for the short moving average.
        long_window: Period for the long moving average.
        state: Optional state abbreviation filter.

    Returns:
        List of CrossoverEvent instances ordered by week.

    Raises:
        CrossoverError: If inputs are invalid or no data found.
    """
    if short_window >= long_window:
        raise CrossoverError(
            f"short_window ({short_window}) must be less than long_window ({long_window})"
        )

    filtered = [
        r
        for r in records
        if r.get("commodity_desc", "").lower() == commodity.lower()
        and (state is None or r.get("state_alpha", "").upper() == state.upper())
    ]

    if not filtered:
        raise CrossoverError(f"No records found for commodity '{commodity}'.")

    filtered.sort(key=lambda r: r.get("week_ending", ""))

    values: List[float] = []
    weeks: List[str] = []
    for r in filtered:
        try:
            values.append(float(r["Value"]))
            weeks.append(r.get("week_ending", ""))
        except (KeyError, ValueError, TypeError):
            continue

    if len(values) < long_window:
        raise CrossoverError(
            f"Not enough data points ({len(values)}) for long_window={long_window}."
        )

    shorts = _rolling_mean(values, short_window)
    longs = _rolling_mean(values, long_window)

    events: List[CrossoverEvent] = []
    for i in range(1, len(values)):
        s_prev, l_prev = shorts[i - 1], longs[i - 1]
        s_cur, l_cur = shorts[i], longs[i]
        if None in (s_prev, l_prev, s_cur, l_cur):
            continue
        if s_prev <= l_prev and s_cur > l_cur:  # type: ignore[operator]
            events.append(CrossoverEvent(weeks[i], "bullish", s_cur, l_cur))  # type: ignore[arg-type]
        elif s_prev >= l_prev and s_cur < l_cur:  # type: ignore[operator]
            events.append(CrossoverEvent(weeks[i], "bearish", s_cur, l_cur))  # type: ignore[arg-type]

    return events


def format_crossovers(events: List[CrossoverEvent], commodity: str) -> str:
    """Return a human-readable table of crossover events."""
    if not events:
        return f"No crossover events detected for {commodity}."

    header = f"Crossover Events — {commodity}"
    sep = "-" * 60
    lines = [header, sep, f"{'Week':<14} {'Signal':<10} {'Short Avg':>10} {'Long Avg':>10}"]
    lines.append(sep)
    for ev in events:
        signal = "▲ Bullish" if ev.direction == "bullish" else "▼ Bearish"
        lines.append(
            f"{ev.week_ending:<14} {signal:<10} {ev.short_avg:>10.1f} {ev.long_avg:>10.1f}"
        )
    lines.append(sep)
    return "\n".join(lines)
