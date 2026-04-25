"""Detect cyclical (repeating) patterns across weeks for a given commodity."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


class CyclicalError(Exception):
    pass


@dataclass
class CyclicalResult:
    commodity: str
    state: str
    period_weeks: int
    peak_weeks: List[int]
    trough_weeks: List[int]
    autocorrelation: float


def _extract_sorted(records: list, commodity: str, state: str) -> List[tuple]:
    """Return (week_ending, value) tuples sorted by week, filtered by commodity/state."""
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
        out.append((r.get("week_ending", ""), val))
    out.sort(key=lambda x: x[0])
    return out


def _autocorrelation(values: List[float], lag: int) -> float:
    """Compute Pearson autocorrelation at the given lag."""
    n = len(values)
    if n <= lag:
        return 0.0
    mean = sum(values) / n
    denom = sum((v - mean) ** 2 for v in values)
    if denom == 0.0:
        return 0.0
    numer = sum((values[i] - mean) * (values[i - lag] - mean) for i in range(lag, n))
    return numer / denom


def detect_cyclical(
    records: list,
    commodity: str,
    state: str = "US",
    max_period: int = 12,
) -> CyclicalResult:
    """Detect the dominant cycle period and return peak/trough week indices."""
    series = _extract_sorted(records, commodity, state)
    if len(series) < 4:
        raise CyclicalError(
            f"Not enough data to detect cycles for '{commodity}' / '{state}'."
        )
    values = [v for _, v in series]
    weeks = [w for w, _ in series]

    # Find the lag with highest autocorrelation
    best_lag = 1
    best_ac = -2.0
    for lag in range(1, min(max_period + 1, len(values))):
        ac = _autocorrelation(values, lag)
        if ac > best_ac:
            best_ac = ac
            best_lag = lag

    # Identify local peaks and troughs
    peak_weeks: List[int] = []
    trough_weeks: List[int] = []
    for i in range(1, len(values) - 1):
        if values[i] > values[i - 1] and values[i] > values[i + 1]:
            peak_weeks.append(i)
        elif values[i] < values[i - 1] and values[i] < values[i + 1]:
            trough_weeks.append(i)

    return CyclicalResult(
        commodity=commodity,
        state=state,
        period_weeks=best_lag,
        peak_weeks=peak_weeks,
        trough_weeks=trough_weeks,
        autocorrelation=round(best_ac, 4),
    )


def format_cyclical(result: CyclicalResult) -> str:
    lines = [
        f"Cyclical Analysis — {result.commodity} ({result.state})",
        "-" * 50,
        f"Dominant period : {result.period_weeks} week(s)",
        f"Autocorrelation : {result.autocorrelation:.4f}",
        f"Peak indices    : {result.peak_weeks or 'none detected'}",
        f"Trough indices  : {result.trough_weeks or 'none detected'}",
    ]
    return "\n".join(lines)
