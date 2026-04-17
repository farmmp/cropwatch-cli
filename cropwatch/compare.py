"""Year-over-year comparison utilities for crop progress data."""

from typing import Optional


class CompareError(Exception):
    pass


def extract_week_value(records: list[dict], week_ending: str, commodity: str) -> Optional[float]:
    """Find the numeric value for a specific week and commodity."""
    for r in records:
        if r.get("week_ending") == week_ending and r.get("commodity_desc") == commodity:
            try:
                return float(r["Value"])
            except (KeyError, ValueError, TypeError):
                return None
    return None


def compare_years(
    current_records: list[dict],
    previous_records: list[dict],
    commodity: str,
    week_ending: str,
) -> dict:
    """Compare a single week's value between two years.

    Returns a dict with current, previous, delta, and pct_change.
    """
    current = extract_week_value(current_records, week_ending, commodity)
    previous = extract_week_value(previous_records, week_ending, commodity)

    if current is None and previous is None:
        raise CompareError(f"No data found for commodity '{commodity}' on week '{week_ending}'.")

    delta = None
    pct_change = None
    if current is not None and previous is not None:
        delta = round(current - previous, 2)
        if previous != 0:
            pct_change = round((delta / previous) * 100, 2)

    return {
        "commodity": commodity,
        "week_ending": week_ending,
        "current": current,
        "previous": previous,
        "delta": delta,
        "pct_change": pct_change,
    }


def format_comparison(result: dict) -> str:
    """Render a comparison result as a human-readable string."""
    lines = [
        f"Commodity : {result['commodity']}",
        f"Week      : {result['week_ending']}",
        f"Current   : {result['current'] if result['current'] is not None else 'N/A'}%",
        f"Previous  : {result['previous'] if result['previous'] is not None else 'N/A'}%",
    ]
    if result["delta"] is not None:
        arrow = "▲" if result["delta"] >= 0 else "▼"
        lines.append(f"Change    : {arrow} {abs(result['delta'])}%")
        if result["pct_change"] is not None:
            lines.append(f"Rel. Chg  : {result['pct_change']:+.2f}%")
    return "\n".join(lines)
