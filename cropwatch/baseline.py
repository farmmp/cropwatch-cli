"""Compute and format baseline (multi-year average) for a crop/week."""
from __future__ import annotations
from dataclasses import dataclass
from statistics import mean, stdev
from typing import List


class BaselineError(Exception):
    pass


@dataclass
class BaselineResult:
    commodity: str
    week_ending: str
    years: List[int]
    average: float
    std_dev: float
    current: float
    delta: float


def compute_baseline(
    records: list[dict],
    commodity: str,
    week_ending: str,
    current_year: int,
    value_key: str = "Value",
) -> BaselineResult:
    """Compare current year value against historical average for the same week."""
    if not records:
        raise BaselineError("No records provided.")

    week_records = [
        r for r in records
        if r.get("commodity_desc", "").lower() == commodity.lower()
        and r.get("week_ending") == week_ending
    ]
    if not week_records:
        raise BaselineError(f"No records found for commodity '{commodity}' week '{week_ending}'.")

    current_records = [r for r in week_records if str(r.get("year")) == str(current_year)]
    if not current_records:
        raise BaselineError(f"No data for current year {current_year}.")

    try:
        current_val = float(current_records[0][value_key])
    except (KeyError, ValueError, TypeError) as e:
        raise BaselineError(f"Invalid current value: {e}") from e

    historical = [
        r for r in week_records if str(r.get("year")) != str(current_year)
    ]
    if not historical:
        raise BaselineError("No historical records to build baseline.")

    values, years = [], []
    for r in historical:
        try:
            values.append(float(r[value_key]))
            years.append(int(r["year"]))
        except (KeyError, ValueError, TypeError):
            continue

    if not values:
        raise BaselineError("No numeric historical values found.")

    avg = mean(values)
    sd = stdev(values) if len(values) > 1 else 0.0
    return BaselineResult(
        commodity=commodity,
        week_ending=week_ending,
        years=sorted(set(years)),
        average=round(avg, 2),
        std_dev=round(sd, 2),
        current=round(current_val, 2),
        delta=round(current_val - avg, 2),
    )


def format_baseline(result: BaselineResult) -> str:
    lines = [
        f"Baseline Report — {result.commodity} | Week: {result.week_ending}",
        "-" * 52,
        f"  Current ({max(result.years) + 1 if result.years else '?'}): {result.current:>6.1f}%",
        f"  Hist. Avg ({len(result.years)} yrs): {result.average:>6.1f}%",
        f"  Std Dev:          {result.std_dev:>6.1f}%",
        f"  Delta:            {result.delta:>+6.1f}%",
    ]
    return "\n".join(lines)
