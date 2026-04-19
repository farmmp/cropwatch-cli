"""Rolling average smoothing for crop progress series."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


class SmoothError(Exception):
    pass


@dataclass
class SmoothedSeries:
    weeks: List[str]
    original: List[float]
    smoothed: List[float]
    window: int


def _rolling_avg(values: List[float], window: int) -> List[float]:
    result = []
    for i, v in enumerate(values):
        start = max(0, i - window + 1)
        chunk = values[start : i + 1]
        result.append(sum(chunk) / len(chunk))
    return result


def smooth_series(records: list, commodity: str, week_field: str = "week_ending",
                 value_field: str = "Value", window: int = 3) -> SmoothedSeries:
    if not records:
        raise SmoothError("No records provided.")
    if window < 1:
        raise SmoothError("Window must be >= 1.")

    filtered = [r for r in records if r.get("commodity_desc", "").upper() == commodity.upper()]
    if not filtered:
        raise SmoothError(f"No records found for commodity '{commodity}'.")

    weeks, original = [], []
    for r in filtered:
        try:
            val = float(r[value_field])
        except (KeyError, ValueError, TypeError):
            continue
        weeks.append(r.get(week_field, ""))
        original.append(val)

    if not original:
        raise SmoothError("No numeric values found in records.")

    smoothed = _rolling_avg(original, window)
    return SmoothedSeries(weeks=weeks, original=original, smoothed=smoothed, window=window)


def format_smooth(series: SmoothedSeries, commodity: str) -> str:
    lines = [
        f"Smoothed Series — {commodity.title()}  (window={series.window})",
        f"{'Week':<14} {'Actual':>8} {'Smoothed':>10}",
        "-" * 36,
    ]
    for w, o, s in zip(series.weeks, series.original, series.smoothed):
        lines.append(f"{w:<14} {o:>8.1f} {s:>10.2f}")
    return "\n".join(lines)
