"""Elasticity module: measures week-over-week sensitivity of crop progress values."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class ElasticityError(Exception):
    pass


@dataclass
class ElasticityResult:
    commodity: str
    state: str
    week_endings: List[str]
    values: List[float]
    elasticities: List[float]  # % change between consecutive weeks
    mean_elasticity: float
    max_elasticity: float
    min_elasticity: float


def _extract_sorted(records: list, commodity: str, state: str) -> List[tuple]:
    """Return (week_ending, value) pairs sorted by week, filtered by commodity/state."""
    out = []
    for r in records:
        if r.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if r.get("state_alpha", "").upper() != state.upper():
            continue
        try:
            val = float(r["Value"])
        except (KeyError, ValueError, TypeError):
            continue
        week = r.get("week_ending", "")
        out.append((week, val))
    return sorted(out, key=lambda x: x[0])


def compute_elasticity(
    records: list,
    commodity: str,
    state: str = "US",
) -> ElasticityResult:
    """Compute week-over-week percentage changes (elasticity) for a series."""
    if not records:
        raise ElasticityError("No records provided.")

    pairs = _extract_sorted(records, commodity, state)
    if len(pairs) < 2:
        raise ElasticityError(
            f"Need at least 2 data points for '{commodity}' / '{state}'; got {len(pairs)}."
        )

    weeks = [p[0] for p in pairs]
    values = [p[1] for p in pairs]

    elasticities: List[float] = []
    for i in range(1, len(values)):
        prev = values[i - 1]
        curr = values[i]
        if prev == 0:
            elasticities.append(0.0)
        else:
            elasticities.append(round((curr - prev) / abs(prev) * 100, 4))

    mean_e = round(sum(elasticities) / len(elasticities), 4)
    return ElasticityResult(
        commodity=commodity,
        state=state,
        week_endings=weeks,
        values=values,
        elasticities=elasticities,
        mean_elasticity=mean_e,
        max_elasticity=max(elasticities),
        min_elasticity=min(elasticities),
    )


def format_elasticity(result: ElasticityResult) -> str:
    lines = [
        f"Elasticity — {result.commodity} | {result.state}",
        f"{'Week':<14} {'Value':>8} {'Δ%':>10}",
        "-" * 36,
    ]
    lines.append(f"{result.week_endings[0]:<14} {result.values[0]:>8.1f} {'—':>10}")
    for i, e in enumerate(result.elasticities):
        week = result.week_endings[i + 1]
        val = result.values[i + 1]
        sign = "+" if e >= 0 else ""
        lines.append(f"{week:<14} {val:>8.1f} {sign}{e:>9.2f}%")
    lines.append("-" * 36)
    lines.append(f"{'Mean Δ%':<14} {result.mean_elasticity:>+.2f}%")
    lines.append(f"{'Max Δ%':<14} {result.max_elasticity:>+.2f}%")
    lines.append(f"{'Min Δ%':<14} {result.min_elasticity:>+.2f}%")
    return "\n".join(lines)
