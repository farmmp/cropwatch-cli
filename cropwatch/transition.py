"""Detect week-over-week state transitions (acceleration/deceleration crossings)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class TransitionError(Exception):
    pass


@dataclass
class TransitionEvent:
    week_ending: str
    from_value: float
    to_value: float
    direction: str   # "up" | "down" | "flat"
    magnitude: float


@dataclass
class TransitionResult:
    commodity: str
    state: str
    events: List[TransitionEvent]
    dominant_direction: str
    avg_magnitude: float


def _extract_sorted(records: list, commodity: str, state: str) -> list:
    out = []
    for r in records:
        if r.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if r.get("state_alpha", "US").upper() != state.upper():
            continue
        try:
            val = float(r["Value"])
        except (KeyError, TypeError, ValueError):
            continue
        out.append((r.get("week_ending", ""), val))
    return sorted(out, key=lambda x: x[0])


def detect_transitions(
    records: list,
    commodity: str,
    state: str = "US",
    threshold: float = 0.0,
) -> TransitionResult:
    if not records:
        raise TransitionError("No records provided.")

    series = _extract_sorted(records, commodity, state)
    if len(series) < 2:
        raise TransitionError(
            f"Need at least 2 data points for '{commodity}' / '{state}'."
        )

    events: List[TransitionEvent] = []
    for (w0, v0), (w1, v1) in zip(series, series[1:]):
        delta = v1 - v0
        mag = abs(delta)
        if mag <= threshold:
            direction = "flat"
        elif delta > 0:
            direction = "up"
        else:
            direction = "down"
        events.append(TransitionEvent(w1, v0, v1, direction, mag))

    counts = {"up": 0, "down": 0, "flat": 0}
    for e in events:
        counts[e.direction] += 1
    dominant = max(counts, key=lambda k: counts[k])
    avg_mag = sum(e.magnitude for e in events) / len(events)

    return TransitionResult(commodity, state, events, dominant, round(avg_mag, 4))


def format_transitions(result: TransitionResult) -> str:
    lines = [
        f"Transitions — {result.commodity} [{result.state}]",
        f"Dominant direction: {result.dominant_direction}  "
        f"Avg magnitude: {result.avg_magnitude:.2f}pp",
        f"{'Week Ending':<14} {'From':>7} {'To':>7} {'Dir':<6} {'Mag':>6}",
        "-" * 46,
    ]
    arrows = {"up": "▲", "down": "▼", "flat": "─"}
    for e in result.events:
        lines.append(
            f"{e.week_ending:<14} {e.from_value:>7.1f} {e.to_value:>7.1f} "
            f"{arrows[e.direction]:<6} {e.magnitude:>6.2f}"
        )
    return "\n".join(lines)
