"""Saturation analysis: detect weeks where crop progress stalls near 0% or 100%."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

SATURATION_LOW = 5.0
SATURATION_HIGH = 95.0


class SaturationError(Exception):
    """Raised when saturation analysis cannot be performed."""


@dataclass
class SaturationResult:
    week_ending: str
    value: float
    kind: str  # "floor" | "ceiling"


def detect_saturation(
    records: list,
    commodity: str,
    attribute: str,
    state: str = "US",
    low: float = SATURATION_LOW,
    high: float = SATURATION_HIGH,
) -> List[SaturationResult]:
    """Return weeks where *attribute* for *commodity* is saturated.

    Args:
        records: Raw USDA API records.
        commodity: Crop name to filter on.
        attribute: Data column to inspect (e.g. ``"Value"``).
        state: State abbreviation; defaults to national (``"US"``).
        low: Threshold below which a value is considered floor-saturated.
        high: Threshold above which a value is considered ceiling-saturated.

    Raises:
        SaturationError: If no matching records are found.
    """
    filtered = [
        r for r in records
        if r.get("commodity_desc", "").upper() == commodity.upper()
        and r.get("state_alpha", "US").upper() == state.upper()
    ]
    if not filtered:
        raise SaturationError(
            f"No records found for commodity={commodity!r} state={state!r}"
        )

    results: List[SaturationResult] = []
    for r in filtered:
        raw = r.get(attribute)
        try:
            val = float(raw)
        except (TypeError, ValueError):
            continue
        if val <= low:
            results.append(SaturationResult(r.get("week_ending", ""), val, "floor"))
        elif val >= high:
            results.append(SaturationResult(r.get("week_ending", ""), val, "ceiling"))

    return results


def format_saturation(results: List[SaturationResult], commodity: str) -> str:
    """Render saturation results as a plain-text table."""
    if not results:
        return f"No saturation detected for {commodity}."

    lines = [
        f"Saturation Report — {commodity}",
        f"{'Week':<14} {'Value':>7}  {'Kind'}",
        "-" * 32,
    ]
    for r in results:
        lines.append(f"{r.week_ending:<14} {r.value:>7.1f}  {r.kind}")
    return "\n".join(lines)
