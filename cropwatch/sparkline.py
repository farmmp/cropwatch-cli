"""Sparkline renderer for crop progress trends."""

SPARK_CHARS = " ▁▂▃▄▅▆▇█"


class SparklineError(Exception):
    pass


def normalize(values: list[float]) -> list[float]:
    """Normalize values to 0-1 range."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def sparkline(values: list[float]) -> str:
    """Return a sparkline string for the given values."""
    if not values:
        raise SparklineError("No values provided for sparkline.")
    normed = normalize(values)
    chars = SPARK_CHARS
    n = len(chars) - 1
    return "".join(chars[round(v * n)] for v in normed)


def format_trend_table(records: list[dict], value_key: str = "Value") -> str:
    """Format a trend table with sparkline for a list of weekly records."""
    if not records:
        return "No trend data available."

    values = []
    for r in records:
        try:
            values.append(float(r[value_key]))
        except (KeyError, TypeError, ValueError):
            values.append(0.0)

    spark = sparkline(values) if values else ""
    weeks = [str(r.get("Week_Ending", "")) for r in records]

    lines = []
    lines.append(f"{'Week':<14} {'Value':>6}")
    lines.append("-" * 22)
    for w, v in zip(weeks, values):
        lines.append(f"{w:<14} {v:>6.1f}")
    lines.append("")
    lines.append(f"Trend: {spark}")
    return "\n".join(lines)
