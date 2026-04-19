"""Compute and format seasonal averages across multiple weeks."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


class SeasonAvgError(Exception):
    pass


@dataclass
class SeasonAvgResult:
    commodity: str
    state: str
    week_count: int
    average: float
    minimum: float
    maximum: float


def compute_season_avg(
    records: list[dict[str, Any]],
    commodity: str,
    state: str = "US",
    value_key: str = "Value",
) -> SeasonAvgResult:
    """Compute seasonal average for a commodity/state pair."""
    if not records:
        raise SeasonAvgError("No records provided")

    values: list[float] = []
    for r in records:
        if r.get("commodity_desc", "").upper() != commodity.upper():
            continue
        if r.get("state_alpha", "US").upper() != state.upper():
            continue
        raw = r.get(value_key, "")
        try:
            values.append(float(str(raw).replace(",", "")))
        except (ValueError, TypeError):
            continue

    if not values:
        raise SeasonAvgError(
            f"No numeric values found for commodity='{commodity}' state='{state}'"
        )

    return SeasonAvgResult(
        commodity=commodity,
        state=state,
        week_count=len(values),
        average=sum(values) / len(values),
        minimum=min(values),
        maximum=max(values),
    )


def format_season_avg(result: SeasonAvgResult) -> str:
    """Render a SeasonAvgResult as a terminal-friendly string."""
    lines = [
        f"Seasonal Average — {result.commodity} ({result.state})",
        "-" * 44,
        f"  Weeks sampled : {result.week_count}",
        f"  Average       : {result.average:.1f}%",
        f"  Minimum       : {result.minimum:.1f}%",
        f"  Maximum       : {result.maximum:.1f}%",
    ]
    return "\n".join(lines)
