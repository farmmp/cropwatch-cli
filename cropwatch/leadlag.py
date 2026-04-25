"""Lead-lag analysis: measure how many weeks one commodity leads or lags another."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class LeadLagError(Exception):
    """Raised when lead-lag computation cannot proceed."""


@dataclass
class LeadLagResult:
    commodity_a: str
    commodity_b: str
    best_lag: int          # positive => A leads B, negative => B leads A
    correlation: float
    max_lag: int


def _extract_sorted(records: list, commodity: str, state: Optional[str]) -> List[float]:
    """Return value series sorted by week_ending for a given commodity/state."""
    filtered = [
        r for r in records
        if r.get("commodity_desc", "") == commodity
        and (state is None or r.get("state_alpha", "") == state)
    ]
    filtered.sort(key=lambda r: r.get("week_ending", ""))
    series: List[float] = []
    for r in filtered:
        try:
            series.append(float(r["Value"]))
        except (KeyError, ValueError, TypeError):
            continue
    return series


def _pearson(a: List[float], b: List[float]) -> float:
    """Compute Pearson correlation between two equal-length lists."""
    n = len(a)
    if n == 0:
        return 0.0
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    num = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    den_a = sum((x - mean_a) ** 2 for x in a) ** 0.5
    den_b = sum((y - mean_b) ** 2 for y in b) ** 0.5
    if den_a == 0 or den_b == 0:
        return 0.0
    return num / (den_a * den_b)


def compute_leadlag(
    records: list,
    commodity_a: str,
    commodity_b: str,
    state: Optional[str] = None,
    max_lag: int = 4,
) -> LeadLagResult:
    """Compute the lag offset that maximises correlation between two commodities."""
    if not records:
        raise LeadLagError("No records provided.")
    series_a = _extract_sorted(records, commodity_a, state)
    series_b = _extract_sorted(records, commodity_b, state)
    if len(series_a) < 2:
        raise LeadLagError(f"Insufficient data for commodity '{commodity_a}'.")
    if len(series_b) < 2:
        raise LeadLagError(f"Insufficient data for commodity '{commodity_b}'.")

    best_lag = 0
    best_corr = -2.0
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            a_slice = series_a[lag:]
            b_slice = series_b[: len(series_a) - lag] if lag > 0 else series_b
        else:
            a_slice = series_a[: len(series_a) + lag]
            b_slice = series_b[-lag:]
        min_len = min(len(a_slice), len(b_slice))
        if min_len < 2:
            continue
        corr = _pearson(a_slice[:min_len], b_slice[:min_len])
        if corr > best_corr:
            best_corr = corr
            best_lag = lag

    return LeadLagResult(
        commodity_a=commodity_a,
        commodity_b=commodity_b,
        best_lag=best_lag,
        correlation=round(best_corr, 4),
        max_lag=max_lag,
    )


def format_leadlag(result: LeadLagResult) -> str:
    """Return a human-readable summary of the lead-lag result."""
    lines = [
        f"Lead-Lag Analysis: {result.commodity_a} vs {result.commodity_b}",
        "-" * 50,
    ]
    if result.best_lag > 0:
        direction = f"{result.commodity_a} leads {result.commodity_b} by {result.best_lag} week(s)"
    elif result.best_lag < 0:
        direction = f"{result.commodity_b} leads {result.commodity_a} by {abs(result.best_lag)} week(s)"
    else:
        direction = "No lead/lag detected (in-phase)"
    lines.append(f"Best lag offset : {result.best_lag:+d}")
    lines.append(f"Correlation     : {result.correlation:.4f}")
    lines.append(f"Interpretation  : {direction}")
    lines.append(f"Max lag tested  : ±{result.max_lag} weeks")
    return "\n".join(lines)
