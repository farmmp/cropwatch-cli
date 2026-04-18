"""Simple linear-extrapolation forecast for crop progress values."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


class ForecastError(Exception):
    pass


@dataclass
class ForecastResult:
    weeks_ahead: int
    predicted_value: float
    slope: float
    intercept: float


def _linear_fit(values: List[float]):
    """Return (slope, intercept) via least-squares on index positions."""
    n = len(values)
    if n < 2:
        raise ForecastError("Need at least 2 data points to fit a trend.")
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    den = sum((x - x_mean) ** 2 for x in xs)
    if den == 0:
        raise ForecastError("All x values identical; cannot compute slope.")
    slope = num / den
    intercept = y_mean - slope * x_mean
    return slope, intercept


def forecast(values: List[float], weeks_ahead: int = 1) -> ForecastResult:
    """Forecast crop progress `weeks_ahead` beyond the last observation."""
    if weeks_ahead < 1:
        raise ForecastError("weeks_ahead must be >= 1.")
    slope, intercept = _linear_fit(values)
    next_x = len(values) - 1 + weeks_ahead
    predicted = slope * next_x + intercept
    predicted = max(0.0, min(100.0, predicted))
    return ForecastResult(
        weeks_ahead=weeks_ahead,
        predicted_value=round(predicted, 2),
        slope=round(slope, 4),
        intercept=round(intercept, 4),
    )


def extract_series(records: list, commodity: str, week_ending: str | None = None) -> List[float]:
    """Pull numeric Value fields for a commodity from USDA records, ordered as given."""
    filtered = [
        r for r in records
        if r.get("commodity_desc", "").lower() == commodity.lower()
        and r.get("Value") not in (None, "", "(D)", "(NA)")
    ]
    if week_ending:
        filtered = [r for r in filtered if r.get("week_ending") == week_ending]
    try:
        return [float(r["Value"]) for r in filtered]
    except (ValueError, KeyError) as exc:
        raise ForecastError(f"Non-numeric value encountered: {exc}") from exc


def format_forecast(result: ForecastResult, commodity: str) -> str:
    lines = [
        f"Forecast for {commodity.title()} (+{result.weeks_ahead} week(s))",
        "-" * 42,
        f"  Predicted value : {result.predicted_value:.1f}%",
        f"  Trend slope     : {result.slope:+.4f} per week",
        f"  Intercept       : {result.intercept:.4f}",
    ]
    return "\n".join(lines)
