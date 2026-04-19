"""State-by-week heatmap rendering for crop progress data."""
from __future__ import annotations
from typing import Any

HEAT_CHARS = " ░▒▓█"


class HeatmapError(Exception):
    pass


def _heat_char(value: float, lo: float, hi: float) -> str:
    if hi == lo:
        return HEAT_CHARS[2]
    ratio = (value - lo) / (hi - lo)
    idx = min(int(ratio * (len(HEAT_CHARS) - 1)), len(HEAT_CHARS) - 1)
    return HEAT_CHARS[idx]


def build_heatmap(records: list[dict[str, Any]], commodity: str, week_desc: str) -> dict[str, float]:
    """Return {state: value} for a given commodity and week_desc."""
    result: dict[str, float] = {}
    for r in records:
        if r.get("commodity_desc") != commodity:
            continue
        if r.get("week_ending") != week_desc and r.get("reference_period_desc") != week_desc:
            continue
        state = r.get("state_alpha", "US")
        try:
            result[state] = float(r["Value"])
        except (KeyError, ValueError, TypeError):
            continue
    if not result:
        raise HeatmapError(f"No data for commodity '{commodity}' on week '{week_desc}'")
    return result


def format_heatmap(state_values: dict[str, float], title: str = "") -> str:
    if not state_values:
        raise HeatmapError("No state values to render")
    lo = min(state_values.values())
    hi = max(state_values.values())
    lines: list[str] = []
    if title:
        lines.append(title)
        lines.append("-" * len(title))
    col_w = 6
    for state in sorted(state_values):
        val = state_values[state]
        ch = _heat_char(val, lo, hi)
        bar = ch * 20
        lines.append(f"{state:<4} {bar}  {val:6.1f}%")
    lines.append(f"\nRange: {lo:.1f}% – {hi:.1f}%")
    return "\n".join(lines)
