"""Threshold-based alerts for crop progress values."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_ALERTS_FILE = Path.home() / ".cropwatch" / "alerts.json"


class AlertError(Exception):
    pass


def _alerts_path(path: Path | None = None) -> Path:
    return path or DEFAULT_ALERTS_FILE


def load_alerts(path: Path | None = None) -> list[dict[str, Any]]:
    """Load saved alert rules from disk."""
    p = _alerts_path(path)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def save_alert(commodity: str, metric: str, threshold: float,
               condition: str = "below", path: Path | None = None) -> dict[str, Any]:
    """Add an alert rule and persist it.

    condition: 'above' | 'below'
    """
    if condition not in ("above", "below"):
        raise AlertError(f"Invalid condition '{condition}'. Use 'above' or 'below'.")

    p = _alerts_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    alerts = load_alerts(path)
    rule: dict[str, Any] = {
        "commodity": commodity,
        "metric": metric,
        "threshold": threshold,
        "condition": condition,
    }
    alerts.append(rule)
    p.write_text(json.dumps(alerts, indent=2))
    return rule


def delete_alert(index: int, path: Path | None = None) -> dict[str, Any]:
    """Remove a single alert rule by its zero-based index.

    Returns the removed rule.
    Raises AlertError if the index is out of range.
    """
    p = _alerts_path(path)
    alerts = load_alerts(path)
    if not 0 <= index < len(alerts):
        raise AlertError(
            f"Alert index {index} is out of range (0-{len(alerts) - 1})." if alerts
            else "No alert rules are saved."
        )
    removed = alerts.pop(index)
    p.write_text(json.dumps(alerts, indent=2))
    return removed


def check_alerts(data: list[dict[str, Any]],
                 path: Path | None = None) -> list[dict[str, Any]]:
    """Check data rows against saved alert rules.

    Returns list of triggered alerts with the offending row attached.
    """
    rules = load_alerts(path)
    triggered = []
    for rule in rules:
        for row in data:
            if row.get("commodity_desc", "").lower() != rule["commodity"].lower():
                continue
            if row.get("short_desc", "").lower().find(rule["metric"].lower()) == -1:
                continue
            try:
                value = float(row.get("Value", 0))
            except (TypeError, ValueError):
                continue
            triggered_flag = (
                (rule["condition"] == "below" and value < rule["threshold"]) or
                (rule["condition"] == "above" and value > rule["threshold"])
            )
            if triggered_flag:
                triggered.append({"rule": rule, "row": row, "value": value})
    return triggered


def clear_alerts(path: Path | None = None) -> None:
    """Delete all saved alert rules."""
    p = _alerts_path(path)
    if p.exists():
        p.unlink()
