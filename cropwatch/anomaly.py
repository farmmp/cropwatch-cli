"""Anomaly detection: flag weeks where value deviates significantly from historical mean."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


class AnomalyError(Exception):
    pass


@dataclass
class Anomaly:
    week_ending: str
    value: float
    mean: float
    deviation: float  # in standard deviations


def _mean_std(values: List[float]):
    if not values:
        raise AnomalyError("No values provided.")
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std = variance ** 0.5
    return mean, std


def detect_anomalies(records: List[dict], value_key: str, threshold: float = 1.5) -> List[Anomaly]:
    """Return records whose value deviates more than *threshold* std devs from the mean."""
    if not records:
        raise AnomalyError("No records provided.")
    numeric = []
    for r in records:
        try:
            numeric.append(float(r[value_key]))
        except (KeyError, TypeError, ValueError):
            pass
    if not numeric:
        raise AnomalyError(f"No numeric values found for key '{value_key}'.")
    mean, std = _mean_std(numeric)
    anomalies = []
    for r in records:
        try:
            val = float(r[value_key])
        except (KeyError, TypeError, ValueError):
            continue
        if std == 0:
            continue
        dev = abs(val - mean) / std
        if dev >= threshold:
            anomalies.append(Anomaly(
                week_ending=r.get("week_ending", "unknown"),
                value=val,
                mean=round(mean, 2),
                deviation=round(dev, 2),
            ))
    return anomalies


def format_anomalies(anomalies: List[Anomaly], value_key: str) -> str:
    if not anomalies:
        return "No anomalies detected."
    lines = [f"{'Week':<14} {'Value':>7} {'Mean':>7} {'StdDevs':>8}",
             "-" * 40]
    for a in anomalies:
        lines.append(f"{a.week_ending:<14} {a.value:>7.1f} {a.mean:>7.1f} {a.deviation:>8.2f}")
    return "\n".join(lines)
