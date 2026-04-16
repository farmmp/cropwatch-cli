"""Local history tracking for crop progress queries."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_HISTORY_DIR = Path.home() / ".cropwatch"
HISTORY_FILE = "history.json"
MAX_ENTRIES = 50


def _history_path(base_dir: Path | None = None) -> Path:
    base = base_dir or DEFAULT_HISTORY_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / HISTORY_FILE


def load_history(base_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load query history from disk. Returns empty list on error."""
    path = _history_path(base_dir)
    if not path.exists():
        return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def record_query(
    commodity: str,
    year: int,
    state: str | None,
    result_count: int,
    base_dir: Path | None = None,
) -> None:
    """Append a query record to history, capping at MAX_ENTRIES."""
    entries = load_history(base_dir)
    entry: dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
        "commodity": commodity,
        "year": year,
        "state": state,
        "result_count": result_count,
    }
    entries.append(entry)
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]
    path = _history_path(base_dir)
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


def clear_history(base_dir: Path | None = None) -> None:
    """Delete all recorded history."""
    path = _history_path(base_dir)
    if path.exists():
        path.unlink()
