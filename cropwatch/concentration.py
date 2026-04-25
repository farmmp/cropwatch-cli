"""Compute Herfindahl-Hirschman Index (HHI) concentration across states."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ConcentrationError(Exception):
    """Raised when concentration computation fails."""


@dataclass
class ConcentrationResult:
    commodity: str
    week_desc: str
    hhi: float  # 0-10000 scale
    top_state: str
    top_share: float  # fraction 0-1
    state_shares: dict[str, float]


def _extract_keyed(
    records: list[dict[str, Any]],
    commodity: str,
    week_desc: str,
) -> dict[str, float]:
    """Return {state: value} for the given commodity/week, excluding US totals."""
    result: dict[str, float] = {}
    for r in records:
        if r.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if r.get("week_ending", "") != week_desc and r.get("week_desc", "") != week_desc:
            continue
        state = r.get("state_alpha", "")
        if not state or state.upper() == "US":
            continue
        try:
            val = float(r["Value"])
        except (KeyError, TypeError, ValueError):
            continue
        result[state] = val
    return result


def compute_concentration(
    records: list[dict[str, Any]],
    commodity: str,
    week_desc: str,
) -> ConcentrationResult:
    """Compute HHI concentration for a commodity in a given week."""
    keyed = _extract_keyed(records, commodity, week_desc)
    if not keyed:
        raise ConcentrationError(
            f"No data for commodity={commodity!r} week={week_desc!r}"
        )
    total = sum(keyed.values())
    if total == 0:
        raise ConcentrationError("Total value is zero; cannot compute shares.")
    shares = {s: v / total for s, v in keyed.items()}
    hhi = sum((sh * 100) ** 2 for sh in shares.values()) / 100  # 0-10000 scale
    top_state = max(shares, key=lambda s: shares[s])
    return ConcentrationResult(
        commodity=commodity,
        week_desc=week_desc,
        hhi=round(hhi, 2),
        top_state=top_state,
        top_share=round(shares[top_state], 4),
        state_shares={s: round(v, 4) for s, v in sorted(shares.items(), key=lambda x: -x[1])},
    )


def format_concentration(result: ConcentrationResult) -> str:
    """Return a human-readable string for the concentration result."""
    lines = [
        f"Concentration — {result.commodity}  (week: {result.week_desc})",
        f"  HHI : {result.hhi:.2f}  (0=perfectly dispersed, 10000=monopoly)",
        f"  Top : {result.top_state} ({result.top_share * 100:.1f}%)",
        "",
        f"  {'State':<8} {'Share':>8}",
        f"  {'-----':<8} {'-----':>8}",
    ]
    for state, share in list(result.state_shares.items())[:10]:
        lines.append(f"  {state:<8} {share * 100:>7.1f}%")
    return "\n".join(lines)
