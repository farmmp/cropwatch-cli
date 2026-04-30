"""Detect weeks where values are clipped at a hard boundary (0 or 100)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class ClippingError(Exception):
    """Raised when clipping detection fails."""


@dataclass
class ClippingResult:
    commodity: str
    state: Optional[str]
    week_ending: str
    value: float
    boundary: str  # 'floor' | 'ceiling'


def _extract_sorted(records: list, commodity: str, state: Optional[str]) -> list:
    out = []
    for r in records:
        if r.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if state and r.get("state_alpha", "").upper() != state.upper():
            continue
        try:
            val = float(r["Value"])
        except (KeyError, ValueError, TypeError):
            continue
        out.append((r.get("week_ending", ""), val))
    out.sort(key=lambda x: x[0])
    return out


def detect_clipping(
    records: list,
    commodity: str,
    state: Optional[str] = None,
    floor: float = 0.0,
    ceiling: float = 100.0,
    min_consecutive: int = 2,
) -> List[ClippingResult]:
    """Return weeks where values are stuck at *floor* or *ceiling* for
    at least *min_consecutive* consecutive weeks."""
    series = _extract_sorted(records, commodity, state)
    if not series:
        raise ClippingError(f"No data found for commodity '{commodity}'.")

    results: List[ClippingResult] = []
    n = len(series)
    i = 0
    while i < n:
        week, val = series[i]
        if val == floor or val == ceiling:
            boundary = "floor" if val == floor else "ceiling"
            run = [series[i]]
            j = i + 1
            while j < n and series[j][1] == val:
                run.append(series[j])
                j += 1
            if len(run) >= min_consecutive:
                for w, v in run:
                    results.append(
                        ClippingResult(
                            commodity=commodity,
                            state=state,
                            week_ending=w,
                            value=v,
                            boundary=boundary,
                        )
                    )
            i = j
        else:
            i += 1
    return results


def format_clipping(results: List[ClippingResult], commodity: str) -> str:
    if not results:
        return f"No clipping detected for {commodity}."
    lines = [f"Clipping Report — {commodity}", "-" * 40]
    for r in results:
        state_label = f" [{r.state}]" if r.state else ""
        lines.append(
            f"  {r.week_ending}{state_label}  {r.value:6.1f}%  ({r.boundary})"
        )
    return "\n".join(lines)
