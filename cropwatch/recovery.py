"""Detect recovery patterns: weeks where a value rebounds after a prior decline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class RecoveryError(Exception):
    """Raised when recovery detection cannot proceed."""


@dataclass
class RecoveryResult:
    week_ending: str
    prior_value: float
    trough_value: float
    recovery_value: float
    drawdown: float        # trough - prior  (negative)
    recovery_gain: float   # recovery - trough  (positive)
    net_change: float      # recovery - prior


def _extract_sorted(records: list, commodity: str, state: Optional[str]) -> list:
    """Return numeric records for commodity/state sorted by week_ending."""
    out = []
    for r in records:
        if r.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if state and r.get("state_alpha", "").upper() != state.upper():
            continue
        raw = r.get("Value", "")
        try:
            val = float(str(raw).replace(",", ""))
        except (ValueError, TypeError):
            continue
        out.append({"week_ending": r.get("week_ending", ""), "value": val})
    out.sort(key=lambda x: x["week_ending"])
    return out


def detect_recoveries(
    records: list,
    commodity: str,
    state: Optional[str] = None,
    min_drawdown: float = 2.0,
    min_recovery: float = 1.0,
) -> List[RecoveryResult]:
    """Identify weeks where a trough is followed by a meaningful recovery.

    A recovery event is defined as three consecutive data points A, B, C where:
      - B < A  (drawdown of at least *min_drawdown* percentage points)
      - C > B  (recovery of at least *min_recovery* percentage points)
    """
    series = _extract_sorted(records, commodity, state)
    if len(series) < 3:
        raise RecoveryError(
            f"Need at least 3 data points for recovery detection, got {len(series)}."
        )

    results: List[RecoveryResult] = []
    for i in range(1, len(series) - 1):
        prior = series[i - 1]
        trough = series[i]
        recovery = series[i + 1]

        drawdown = trough["value"] - prior["value"]
        gain = recovery["value"] - trough["value"]

        if drawdown <= -abs(min_drawdown) and gain >= abs(min_recovery):
            results.append(
                RecoveryResult(
                    week_ending=recovery["week_ending"],
                    prior_value=prior["value"],
                    trough_value=trough["value"],
                    recovery_value=recovery["value"],
                    drawdown=drawdown,
                    recovery_gain=gain,
                    net_change=recovery["value"] - prior["value"],
                )
            )
    return results


def format_recoveries(results: List[RecoveryResult], commodity: str) -> str:
    """Render recovery events as a plain-text table."""
    if not results:
        return f"No recovery events detected for {commodity}."

    header = f"Recovery Events — {commodity}\n"
    header += f"{'Week':<14} {'Prior':>7} {'Trough':>7} {'Recover':>8} {'Drawdn':>8} {'Gain':>7} {'Net':>7}\n"
    header += "-" * 62 + "\n"
    rows = []
    for r in results:
        rows.append(
            f"{r.week_ending:<14} {r.prior_value:>7.1f} {r.trough_value:>7.1f} "
            f"{r.recovery_value:>8.1f} {r.drawdown:>8.1f} {r.recovery_gain:>7.1f} {r.net_change:>7.1f}"
        )
    return header + "\n".join(rows)
