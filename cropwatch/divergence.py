"""Compute divergence between two crop progress series (e.g. two states or commodities)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


class DivergenceError(Exception):
    """Raised when divergence computation fails."""


@dataclass
class DivergenceResult:
    week_end: str
    value_a: float
    value_b: float
    delta: float  # value_a - value_b


def _extract_keyed(records: list, label: str, commodity: str, state: str | None) -> dict[str, float]:
    """Return {week_end: value} for the given label/commodity/state."""
    out: dict[str, float] = {}
    for rec in records:
        if rec.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if rec.get("short_desc", "").lower() != label.lower():
            continue
        if state and rec.get("state_alpha", "").upper() != state.upper():
            continue
        week = rec.get("week_ending")
        raw = rec.get("Value")
        if week is None or raw is None:
            continue
        try:
            out[week] = float(str(raw).replace(",", ""))
        except ValueError:
            continue
    return out


def compute_divergence(
    records: list,
    label: str,
    commodity: str,
    state_a: str,
    state_b: str,
) -> List[DivergenceResult]:
    """Compute week-by-week divergence between state_a and state_b.

    Returns results only for weeks present in both series, sorted by week_ending.
    Raises DivergenceError when no overlapping weeks are found.
    """
    if not records:
        raise DivergenceError("No records provided.")

    series_a = _extract_keyed(records, label, commodity, state_a)
    series_b = _extract_keyed(records, label, commodity, state_b)

    common_weeks = sorted(set(series_a) & set(series_b))
    if not common_weeks:
        raise DivergenceError(
            f"No overlapping weeks found for '{state_a}' and '{state_b}' "
            f"with commodity='{commodity}', label='{label}'."
        )

    return [
        DivergenceResult(
            week_end=w,
            value_a=series_a[w],
            value_b=series_b[w],
            delta=round(series_a[w] - series_b[w], 2),
        )
        for w in common_weeks
    ]


def format_divergence(
    results: List[DivergenceResult],
    state_a: str,
    state_b: str,
) -> str:
    """Return a formatted table of divergence results."""
    header = f"{'Week':<14} {state_a.upper():>8} {state_b.upper():>8} {'Delta':>8}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in results:
        sign = "+" if r.delta >= 0 else ""
        lines.append(
            f"{r.week_end:<14} {r.value_a:>8.1f} {r.value_b:>8.1f} {sign}{r.delta:>7.1f}"
        )
    return "\n".join(lines)
