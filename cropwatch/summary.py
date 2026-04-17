"""Summary statistics for crop progress data."""
from __future__ import annotations
from typing import Any


class SummaryError(Exception):
    pass


def compute_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute min, max, average, and latest value from a list of records."""
    if not records:
        raise SummaryError("No records provided for summary.")

    values: list[float] = []
    for r in records:
        raw = r.get("Value")
        if raw is None:
            continue
        try:
            values.append(float(raw))
        except (TypeError, ValueError):
            continue

    if not values:
        raise SummaryError("No numeric values found in records.")

    return {
        "min": min(values),
        "max": max(values),
        "avg": round(sum(values) / len(values), 2),
        "latest": values[-1],
        "count": len(values),
    }


def format_summary(summary: dict[str, Any], commodity: str = "", unit: str = "%") -> str:
    """Return a formatted string for a summary dict."""
    lines = []
    header = f"Summary: {commodity}" if commodity else "Summary"
    lines.append(header)
    lines.append("-" * len(header))
    lines.append(f"  Count   : {summary['count']}")
    lines.append(f"  Latest  : {summary['latest']}{unit}")
    lines.append(f"  Average : {summary['avg']}{unit}")
    lines.append(f"  Min     : {summary['min']}{unit}")
    lines.append(f"  Max     : {summary['max']}{unit}")
    return "\n".join(lines)
