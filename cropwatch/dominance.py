"""Dominance analysis: find which state leads a commodity metric week-over-week."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class DominanceError(Exception):
    """Raised when dominance computation fails."""


@dataclass
class DominanceResult:
    state: str
    commodity: str
    attribute: str
    weeks_leading: int
    avg_value: float
    max_value: float


def _extract_keyed(
    records: list[dict],
    commodity: str,
    attribute: str,
) -> dict[str, list[tuple[int, float]]]:
    """Return {state: [(week, value), ...]} sorted by week."""
    result: dict[str, list[tuple[int, float]]] = {}
    for r in records:
        if r.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if r.get("short_desc", "").lower().find(attribute.lower()) == -1:
            continue
        state = r.get("state_alpha", "")
        if not state or state.upper() == "US":
            continue
        try:
            week = int(r["week_ending"].replace("-", ""))
            value = float(r["Value"])
        except (KeyError, ValueError, TypeError):
            continue
        result.setdefault(state, []).append((week, value))
    for state in result:
        result[state].sort(key=lambda x: x[0])
    return result


def compute_dominance(
    records: list[dict],
    commodity: str,
    attribute: str,
    top_n: int = 5,
) -> list[DominanceResult]:
    """Rank states by how often they hold the highest weekly value."""
    if not records:
        raise DominanceError("No records provided.")

    keyed = _extract_keyed(records, commodity, attribute)
    if not keyed:
        raise DominanceError(
            f"No state-level data found for commodity='{commodity}' attribute='{attribute}'."
        )

    # Collect all weeks present
    all_weeks: set[int] = set()
    for series in keyed.values():
        all_weeks.update(w for w, _ in series)

    lead_counts: dict[str, int] = {state: 0 for state in keyed}
    for week in all_weeks:
        week_vals: dict[str, float] = {}
        for state, series in keyed.items():
            for w, v in series:
                if w == week:
                    week_vals[state] = v
                    break
        if not week_vals:
            continue
        leader = max(week_vals, key=lambda s: week_vals[s])
        lead_counts[leader] += 1

    results: list[DominanceResult] = []
    for state, count in lead_counts.items():
        vals = [v for _, v in keyed[state]]
        results.append(
            DominanceResult(
                state=state,
                commodity=commodity,
                attribute=attribute,
                weeks_leading=count,
                avg_value=round(sum(vals) / len(vals), 2),
                max_value=round(max(vals), 2),
            )
        )

    results.sort(key=lambda r: r.weeks_leading, reverse=True)
    return results[:top_n]


def format_dominance(results: list[DominanceResult]) -> str:
    """Return a formatted table of dominance results."""
    if not results:
        return "No dominance data."
    header = f"{'State':<8} {'Weeks Leading':>13} {'Avg Value':>10} {'Max Value':>10}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in results:
        lines.append(
            f"{r.state:<8} {r.weeks_leading:>13} {r.avg_value:>10.2f} {r.max_value:>10.2f}"
        )
    return "\n".join(lines)
