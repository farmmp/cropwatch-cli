"""Detect rebound patterns: weeks where a value drops then recovers above prior level."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ReboundError(Exception):
    pass


@dataclass
class ReboundResult:
    commodity: str
    state: str
    week_start: int      # week_ending value where the dip begins
    week_recover: int    # week_ending value where recovery is confirmed
    dip_value: float
    recover_value: float
    prior_value: float
    depth: float         # prior_value - dip_value
    gain: float          # recover_value - prior_value


def _extract_sorted(
    records: list[dict[str, Any]],
    commodity: str,
    state: str,
) -> list[tuple[int, float]]:
    """Return (week_ending, value) pairs sorted by week for the given commodity/state."""
    out: list[tuple[int, float]] = []
    for r in records:
        if r.get("commodity_desc") != commodity:
            continue
        if r.get("state_alpha") != state:
            continue
        try:
            week = int(r["week_ending"].replace("-", ""))
            val = float(r["Value"])
        except (KeyError, TypeError, ValueError):
            continue
        out.append((week, val))
    out.sort(key=lambda x: x[0])
    return out


def detect_rebounds(
    records: list[dict[str, Any]],
    commodity: str,
    state: str = "US",
    min_depth: float = 2.0,
) -> list[ReboundResult]:
    """Detect rebound events in the series.

    A rebound is defined as: value[i] > value[i-1], value[i-1] < value[i-2],
    and value[i] > value[i-2] (recovery surpasses the prior peak).
    Only rebounds where the dip depth >= min_depth are returned.
    """
    series = _extract_sorted(records, commodity, state)
    if len(series) < 3:
        raise ReboundError(
            f"Need at least 3 data points for rebound detection; got {len(series)}."
        )
    results: list[ReboundResult] = []
    for i in range(2, len(series)):
        w0, v0 = series[i - 2]
        w1, v1 = series[i - 1]
        w2, v2 = series[i]
        if v1 < v0 and v2 > v0:
            depth = v0 - v1
            if depth >= min_depth:
                results.append(
                    ReboundResult(
                        commodity=commodity,
                        state=state,
                        week_start=w0,
                        week_recover=w2,
                        dip_value=v1,
                        recover_value=v2,
                        prior_value=v0,
                        depth=round(depth, 2),
                        gain=round(v2 - v0, 2),
                    )
                )
    return results


def format_rebounds(results: list[ReboundResult], commodity: str, state: str) -> str:
    """Format rebound results as a terminal-friendly table."""
    if not results:
        return f"No rebounds detected for {commodity} / {state}.\n"
    header = f"Rebound Detection — {commodity} ({state})\n"
    sep = "-" * 62 + "\n"
    col = f"{'Week Dip':<12} {'Week Recover':<14} {'Prior':>7} {'Dip':>7} {'Recover':>9} {'Depth':>7} {'Gain':>7}\n"
    rows = "".join(
        f"{str(r.week_start):<12} {str(r.week_recover):<14} {r.prior_value:>7.1f} "
        f"{r.dip_value:>7.1f} {r.recover_value:>9.1f} {r.depth:>7.1f} {r.gain:>7.1f}\n"
        for r in results
    )
    return header + sep + col + sep + rows
