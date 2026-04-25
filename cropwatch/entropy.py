"""Entropy analysis: measure distribution spread across states for a commodity/week."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


class EntropyError(Exception):
    """Raised when entropy computation fails."""


@dataclass
class EntropyResult:
    commodity: str
    week_ending: str
    state_values: dict[str, float]
    entropy: float
    max_entropy: float
    normalized_entropy: float  # 0-1, 1 = perfectly uniform


def _extract_keyed(
    records: list[dict],
    commodity: str,
    week_ending: str,
) -> dict[str, float]:
    """Return {state: value} for the given commodity and week, excluding 'US'."""
    result: dict[str, float] = {}
    for rec in records:
        if rec.get("commodity_desc", "").lower() != commodity.lower():
            continue
        if rec.get("week_ending") != week_ending:
            continue
        state = rec.get("state_alpha", "")
        if state in ("", "US"):
            continue
        try:
            val = float(rec["Value"])
        except (KeyError, TypeError, ValueError):
            continue
        if val < 0:
            continue
        result[state] = val
    return result


def compute_entropy(
    records: list[dict],
    commodity: str,
    week_ending: str,
) -> EntropyResult:
    """Compute Shannon entropy of state-level values for a commodity/week."""
    if not records:
        raise EntropyError("No records provided.")

    state_values = _extract_keyed(records, commodity, week_ending)
    if not state_values:
        raise EntropyError(
            f"No valid state data for commodity='{commodity}' week='{week_ending}'."
        )

    total = sum(state_values.values())
    if total == 0:
        raise EntropyError("All state values are zero; entropy is undefined.")

    probs = [v / total for v in state_values.values()]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    max_entropy = math.log2(len(state_values))
    normalized = entropy / max_entropy if max_entropy > 0 else 0.0

    return EntropyResult(
        commodity=commodity,
        week_ending=week_ending,
        state_values=state_values,
        entropy=round(entropy, 4),
        max_entropy=round(max_entropy, 4),
        normalized_entropy=round(normalized, 4),
    )


def format_entropy(result: EntropyResult) -> str:
    """Format an EntropyResult as a human-readable string."""
    lines = [
        f"Entropy Analysis — {result.commodity} | Week: {result.week_ending}",
        f"  States analysed : {len(result.state_values)}",
        f"  Shannon entropy : {result.entropy:.4f} bits",
        f"  Max entropy     : {result.max_entropy:.4f} bits",
        f"  Normalised      : {result.normalized_entropy:.4f}  "
        f"({'uniform' if result.normalized_entropy > 0.9 else 'concentrated'})",
    ]
    return "\n".join(lines)
