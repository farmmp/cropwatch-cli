"""Week-over-week moving average deviation analysis."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


class MovingAvgError(Exception):
    pass


@dataclass
class MovingAvgResult:
    week_ending: str
    value: float
    avg: float
    deviation: float


def compute_moving_avg(
    records: list,
    commodity: str,
    attribute: str,
    window: int = 4,
    state: str | None = None,
) -> List[MovingAvgResult]:
    if not records:
        raise MovingAvgError("No records provided.")
    if window < 1:
        raise MovingAvgError("Window must be >= 1.")

    filtered = [
        r for r in records
        if r.get("commodity_desc") == commodity
        and r.get("statisticcat_desc") == attribute
        and (state is None or r.get("state_alpha") == state)
        and r.get("unit_desc") == "PCT"
    ]
    if not filtered:
        raise MovingAvgError(f"No data for commodity={commodity!r} attribute={attribute!r}.")

    series = []
    for r in filtered:
        try:
            series.append((r.get("week_ending", ""), float(r["Value"])))
        except (KeyError, ValueError):
            continue

    series.sort(key=lambda x: x[0])
    if not series:
        raise MovingAvgError("No numeric values found.")

    results = []
    for i, (week, val) in enumerate(series):
        window_vals = [v for _, v in series[max(0, i - window + 1): i + 1]]
        avg = sum(window_vals) / len(window_vals)
        results.append(MovingAvgResult(week_ending=week, value=val, avg=round(avg, 2), deviation=round(val - avg, 2)))
    return results


def format_moving_avg(results: List[MovingAvgResult]) -> str:
    header = f"{'Week':<14} {'Value':>7} {'Avg':>7} {'Dev':>7}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in results:
        lines.append(f"{r.week_ending:<14} {r.value:>7.1f} {r.avg:>7.1f} {r.deviation:>+7.1f}")
    return "\n".join(lines)
