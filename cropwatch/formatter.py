"""Format crop progress data for terminal display."""

from typing import Any

TRENDS = {
    "Excellent": "🟢",
    "Good": "🔵",
    "Fair": "🟡",
    "Poor": "🟠",
    "Very Poor": "🔴",
}

BAR_WIDTH = 30


def _bar(value: float, width: int = BAR_WIDTH) -> str:
    filled = int(round(value / 100 * width))
    return "█" * filled + "░" * (width - filled)


def format_crop_progress(data: list[dict[str, Any]], crop: str, year: int) -> str:
    """Return a formatted string table of crop condition percentages."""
    rows = [
        r for r in data
        if str(r.get("year")) == str(year) and r.get("commodity_desc", "").lower() == crop.lower()
    ]

    if not rows:
        return f"No data found for crop '{crop}' in {year}."

    # Group by week_ending
    weeks: dict[str, dict[str, float]] = {}
    for row in rows:
        week = row.get("week_ending", "Unknown")
        condition = row.get("short_desc", "").split(" - ")[-1].strip()
        value = float(row.get("Value", 0) or 0)
        weeks.setdefault(week, {})[condition] = value

    lines: list[str] = [
        f"\n{'='*60}",
        f"  Crop Progress: {crop.title()} ({year})",
        f"{'='*60}",
    ]

    for week in sorted(weeks.keys(), reverse=True)[:8]:
        lines.append(f"\n  Week ending: {week}")
        lines.append(f"  {'-'*56}")
        conditions = weeks[week]
        for condition, icon in TRENDS.items():
            pct = conditions.get(condition, 0.0)
            bar = _bar(pct)
            lines.append(f"  {icon} {condition:<12} {bar} {pct:5.1f}%")

    lines.append(f"\n{'='*60}\n")
    return "\n".join(lines)


def format_simple_table(data: list[dict[str, Any]], fields: list[str]) -> str:
    """Generic table formatter for arbitrary USDA response fields."""
    if not data:
        return "No data available."

    col_widths = {f: max(len(f), max(len(str(row.get(f, ""))) for row in data)) for f in fields}
    header = "  ".join(f.upper().ljust(col_widths[f]) for f in fields)
    separator = "  ".join("-" * col_widths[f] for f in fields)
    rows = [
        "  ".join(str(row.get(f, "")).ljust(col_widths[f]) for f in fields)
        for row in data
    ]
    return "\n".join([header, separator] + rows)
