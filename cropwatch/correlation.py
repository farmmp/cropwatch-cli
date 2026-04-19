"""Correlation analysis between two crop commodities over time."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
import math


class CorrelationError(Exception):
    pass


@dataclass
class CorrelationResult:
    commodity_a: str
    commodity_b: str
    r: float
    n: int


def _extract_series(records: list, commodity: str, week_key: str = "week_ending") -> dict:
    """Return {week: value} for a given commodity."""
    series: dict = {}
    for rec in records:
        if rec.get("commodity_desc", "").lower() == commodity.lower():
            week = rec.get(week_key)
            try:
                val = float(rec.get("Value", ""))
            except (TypeError, ValueError):
                continue
            if week:
                series[week] = val
    return series


def correlate(records: list, commodity_a: str, commodity_b: str) -> CorrelationResult:
    """Compute Pearson r between two commodities using shared weeks."""
    if not records:
        raise CorrelationError("No records provided.")
    sa = _extract_series(records, commodity_a)
    sb = _extract_series(records, commodity_b)
    weeks = sorted(set(sa) & set(sb))
    if len(weeks) < 3:
        raise CorrelationError(
            f"Not enough shared data points ({len(weeks)}) to correlate "
            f"'{commodity_a}' and '{commodity_b}'."
        )
    xs = [sa[w] for w in weeks]
    ys = [sb[w] for w in weeks]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    if den == 0:
        raise CorrelationError("Zero variance — cannot compute correlation.")
    return CorrelationResult(commodity_a=commodity_a, commodity_b=commodity_b, r=round(num / den, 4), n=n)


def format_correlation(result: CorrelationResult) -> str:
    """Return a human-readable correlation summary."""
    strength = (
        "strong" if abs(result.r) >= 0.7
        else "moderate" if abs(result.r) >= 0.4
        else "weak"
    )
    direction = "positive" if result.r >= 0 else "negative"
    lines = [
        f"Correlation: {result.commodity_a}  vs  {result.commodity_b}",
        "-" * 48,
        f"  Pearson r : {result.r:+.4f}",
        f"  Strength  : {strength} {direction}",
        f"  Weeks used: {result.n}",
    ]
    return "\n".join(lines)
