"""Detect market/growth regime shifts in crop progress data.

A regime is a sustained period where values stay above or below
the series mean. Transitions between regimes are 'regime shifts'.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class RegimeError(Exception):
    """Raised when regime detection fails."""


@dataclass
class RegimeResult:
    commodity: str
    state: Optional[str]
    week_ending: str
    value: float
    regime: str  # 'above' | 'below' | 'neutral'
    shift: bool  # True when regime changed from previous row


def _extract_sorted(
    records: list,
    commodity: str,
    state: Optional[str] = None,
) -> list:
    """Filter and sort records for the given commodity/state."""
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
        out.append((r.get("week_ending", ""), val, r))
    out.sort(key=lambda x: x[0])
    return out


def detect_regimes(
    records: list,
    commodity: str,
    state: Optional[str] = None,
    threshold: float = 0.0,
) -> List[RegimeResult]:
    """Detect regime shifts in a crop progress series.

    Args:
        records: Raw USDA API records.
        commodity: Commodity name to filter on.
        state: Optional state abbreviation filter.
        threshold: Dead-zone around mean; values within ±threshold
                   of the mean are labelled 'neutral'.

    Returns:
        List of RegimeResult, one per data point.
    """
    rows = _extract_sorted(records, commodity, state)
    if not rows:
        raise RegimeError(
            f"No numeric data found for commodity '{commodity}'"
            + (f" in state '{state}'" if state else "")
        )

    mean = sum(v for _, v, _ in rows) / len(rows)

    results: List[RegimeResult] = []
    prev_regime: Optional[str] = None
    for week, val, _ in rows:
        if val > mean + threshold:
            regime = "above"
        elif val < mean - threshold:
            regime = "below"
        else:
            regime = "neutral"
        shift = prev_regime is not None and regime != prev_regime
        results.append(
            RegimeResult(
                commodity=commodity,
                state=state,
                week_ending=week,
                value=val,
                regime=regime,
                shift=shift,
            )
        )
        prev_regime = regime
    return results


def format_regimes(results: List[RegimeResult]) -> str:
    """Return a human-readable table of regime results."""
    header = f"{'Week':<14} {'Value':>7}  {'Regime':<8}  Shift"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in results:
        shift_marker = "<< SHIFT" if r.shift else ""
        lines.append(
            f"{r.week_ending:<14} {r.value:>7.1f}  {r.regime:<8}  {shift_marker}"
        )
    return "\n".join(lines)
