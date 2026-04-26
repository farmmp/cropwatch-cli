"""Skewness analysis: measure asymmetry in crop progress distributions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class SkewnessError(Exception):
    """Raised when skewness computation fails."""


@dataclass
class SkewnessResult:
    commodity: str
    state: Optional[str]
    week_ending: str
    n: int
    mean: float
    skewness: float
    interpretation: str


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _std(values: List[float], mu: float) -> float:
    variance = sum((v - mu) ** 2 for v in values) / len(values)
    return variance ** 0.5


def _skew(values: List[float]) -> float:
    """Compute sample skewness using the adjusted Fisher-Pearson formula."""
    n = len(values)
    if n < 3:
        raise SkewnessError("At least 3 data points required to compute skewness.")
    mu = _mean(values)
    sigma = _std(values, mu)
    if sigma == 0:
        return 0.0
    m3 = sum((v - mu) ** 3 for v in values) / n
    return m3 / (sigma ** 3)


def compute_skewness(
    records: List[dict],
    commodity: str,
    state: Optional[str] = None,
) -> SkewnessResult:
    """Compute skewness of Value across all records for a commodity/state."""
    if not records:
        raise SkewnessError("No records provided.")

    filtered = [
        r for r in records
        if r.get("commodity_desc", "").lower() == commodity.lower()
        and (state is None or r.get("state_alpha", "").upper() == state.upper())
    ]
    values = []
    for r in filtered:
        try:
            values.append(float(r["Value"]))
        except (KeyError, ValueError, TypeError):
            continue

    if len(values) < 3:
        raise SkewnessError(
            f"Not enough numeric records for '{commodity}' "
            f"(state={state}): found {len(values)}, need ≥3."
        )

    week = filtered[-1].get("week_ending", "unknown")
    mu = _mean(values)
    skew = _skew(values)

    if skew > 0.5:
        interpretation = "right-skewed (tail toward high values)"
    elif skew < -0.5:
        interpretation = "left-skewed (tail toward low values)"
    else:
        interpretation = "approximately symmetric"

    return SkewnessResult(
        commodity=commodity,
        state=state,
        week_ending=week,
        n=len(values),
        mean=round(mu, 2),
        skewness=round(skew, 4),
        interpretation=interpretation,
    )


def format_skewness(result: SkewnessResult) -> str:
    """Return a human-readable summary of a SkewnessResult."""
    scope = result.state if result.state else "US (all states)"
    lines = [
        f"Skewness Report — {result.commodity} | {scope}",
        "-" * 48,
        f"  Week Ending : {result.week_ending}",
        f"  N           : {result.n}",
        f"  Mean        : {result.mean:.2f}%",
        f"  Skewness    : {result.skewness:+.4f}",
        f"  Shape       : {result.interpretation}",
    ]
    return "\n".join(lines)
