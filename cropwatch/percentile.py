"""Percentile ranking of crop progress values across states."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any


class PercentileError(Exception):
    pass


@dataclass
class PercentileResult:
    state_desc: str
    value: float
    percentile: float  # 0-100


def compute_percentiles(
    records: List[Dict[str, Any]],
    commodity: str,
    week_ending: str,
    attribute: str = "Value",
) -> List[PercentileResult]:
    """Return percentile results for each state for a given commodity/week."""
    if not records:
        raise PercentileError("No records provided.")

    filtered = [
        r for r in records
        if r.get("commodity_desc", "").lower() == commodity.lower()
        and r.get("week_ending") == week_ending
        and r.get("state_alpha", "US") != "US"
    ]

    values: List[tuple[str, float]] = []
    for r in filtered:
        try:
            v = float(r[attribute])
            values.append((r.get("state_alpha", "?"), v))
        except (KeyError, ValueError, TypeError):
            continue

    if not values:
        raise PercentileError(
            f"No numeric '{attribute}' data found for {commodity} on {week_ending}."
        )

    sorted_vals = sorted(v for _, v in values)
    n = len(sorted_vals)

    results = []
    for state, val in sorted(values, key=lambda x: x[1], reverse=True):
        rank = sorted_vals.index(val)
        pct = (rank / (n - 1) * 100) if n > 1 else 100.0
        results.append(PercentileResult(state_desc=state, value=val, percentile=round(pct, 1)))

    return results


def format_percentiles(results: List[PercentileResult], commodity: str, week_ending: str) -> str:
    lines = [
        f"Percentile Ranking — {commodity.title()} | Week ending {week_ending}",
        f"{'State':<8} {'Value':>8} {'Percentile':>12}",
        "-" * 32,
    ]
    for r in results:
        lines.append(f"{r.state_desc:<8} {r.value:>8.1f} {r.percentile:>11.1f}%")
    return "\n".join(lines)
