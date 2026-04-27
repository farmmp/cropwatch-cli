"""Kurtosis analysis: measures the 'tailedness' of crop progress distributions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


class KurtosisError(Exception):
    pass


@dataclass
class KurtosisResult:
    commodity: str
    state: str
    week_ending: str
    n: int
    mean: float
    std: float
    kurtosis: float
    label: str


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _std(values: List[float], mu: float) -> float:
    variance = sum((v - mu) ** 2 for v in values) / len(values)
    return variance ** 0.5


def _kurt(values: List[float], mu: float, sigma: float) -> float:
    if sigma == 0:
        raise KurtosisError("Standard deviation is zero; kurtosis undefined.")
    n = len(values)
    fourth = sum((v - mu) ** 4 for v in values) / n
    return (fourth / sigma ** 4) - 3.0  # excess kurtosis


def compute_kurtosis(
    records: List[Dict],
    commodity: str,
    state: str = "US",
) -> KurtosisResult:
    """Compute excess kurtosis over weekly values for a commodity/state pair."""
    if not records:
        raise KurtosisError("No records provided.")

    values = []
    week_ending = ""
    for r in records:
        if r.get("commodity_desc", "").upper() != commodity.upper():
            continue
        if r.get("state_alpha", "").upper() != state.upper():
            continue
        try:
            values.append(float(r["Value"]))
        except (KeyError, ValueError, TypeError):
            continue
        week_ending = r.get("week_ending", week_ending)

    if len(values) < 4:
        raise KurtosisError(
            f"Need at least 4 data points for kurtosis; got {len(values)}."
        )

    mu = _mean(values)
    sigma = _std(values, mu)
    k = _kurt(values, mu, sigma)

    if k > 1.0:
        label = "leptokurtic"
    elif k < -1.0:
        label = "platykurtic"
    else:
        label = "mesokurtic"

    return KurtosisResult(
        commodity=commodity,
        state=state,
        week_ending=week_ending,
        n=len(values),
        mean=round(mu, 4),
        std=round(sigma, 4),
        kurtosis=round(k, 4),
        label=label,
    )


def format_kurtosis(result: KurtosisResult) -> str:
    lines = [
        f"Kurtosis Report — {result.commodity} / {result.state}",
        f"  Week ending : {result.week_ending}",
        f"  N           : {result.n}",
        f"  Mean        : {result.mean:.2f}",
        f"  Std Dev     : {result.std:.2f}",
        f"  Excess Kurt : {result.kurtosis:+.4f}  ({result.label})",
    ]
    return "\n".join(lines)
