"""Detect weeks where the spread between high/low progress values is compressing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class CompressionError(Exception):
    pass


@dataclass
class CompressionResult:
    commodity: str
    state: str
    week: str
    spread: float
    prev_spread: float
    delta: float  # negative means compressing


def _extract_sorted(records: list, commodity: str, state: str) -> list:
    out = []
    for r in records:
        if r.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if state and r.get("state_alpha", "").upper() != state.upper():
            continue
        try:
            val = float(r["Value"])
        except (KeyError, ValueError, TypeError):
            continue
        out.append({"week": r.get("week_ending", ""), "value": val, "unit": r.get("unit_desc", "")})
    return sorted(out, key=lambda x: x["week"])


def compute_compression(
    records: list,
    commodity: str,
    state: str = "",
    high_unit: str = "PCT EXCELLENT",
    low_unit: str = "PCT POOR",
    threshold: float = 0.0,
) -> List[CompressionResult]:
    """Return weeks where the high-low spread is narrowing vs the previous week."""
    if not records:
        raise CompressionError("No records provided.")

    high = {r["week"]: r["value"] for r in _extract_sorted(
        [x for x in records if x.get("unit_desc", "") == high_unit], commodity, state
    )}
    low = {r["week"]: r["value"] for r in _extract_sorted(
        [x for x in records if x.get("unit_desc", "") == low_unit], commodity, state
    )}

    weeks = sorted(set(high) & set(low))
    if len(weeks) < 2:
        raise CompressionError("Not enough overlapping weeks to compute compression.")

    results: List[CompressionResult] = []
    prev_spread: Optional[float] = None
    for week in weeks:
        spread = high[week] - low[week]
        if prev_spread is not None:
            delta = spread - prev_spread
            if delta < threshold:
                results.append(CompressionResult(
                    commodity=commodity,
                    state=state or "US",
                    week=week,
                    spread=round(spread, 2),
                    prev_spread=round(prev_spread, 2),
                    delta=round(delta, 2),
                ))
        prev_spread = spread
    return results


def format_compression(results: List[CompressionResult], commodity: str) -> str:
    if not results:
        return f"No spread compression detected for {commodity}."
    lines = [f"Spread Compression — {commodity}", "-" * 46]
    lines.append(f"  {'Week':<14} {'State':<6} {'Spread':>8} {'Prev':>8} {'Delta':>8}")
    for r in results:
        lines.append(f"  {r.week:<14} {r.state:<6} {r.spread:>8.2f} {r.prev_spread:>8.2f} {r.delta:>8.2f}")
    return "\n".join(lines)
