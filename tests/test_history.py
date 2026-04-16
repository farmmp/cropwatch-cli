"""Tests for cropwatch.history module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cropwatch.history import (
    MAX_ENTRIES,
    clear_history,
    load_history,
    record_query,
)


@pytest.fixture
def hist_dir(tmp_path: Path) -> Path:
    return tmp_path / "history"


def test_load_history_empty(hist_dir: Path) -> None:
    assert load_history(hist_dir) == []


def test_record_and_load(hist_dir: Path) -> None:
    record_query("CORN", 2024, None, 10, hist_dir)
    entries = load_history(hist_dir)
    assert len(entries) == 1
    e = entries[0]
    assert e["commodity"] == "CORN"
    assert e["year"] == 2024
    assert e["state"] is None
    assert e["result_count"] == 10
    assert "timestamp" in e


def test_record_with_state(hist_dir: Path) -> None:
    record_query("SOYBEANS", 2023, "IA", 5, hist_dir)
    entries = load_history(hist_dir)
    assert entries[0]["state"] == "IA"


def test_history_capped_at_max(hist_dir: Path) -> None:
    for i in range(MAX_ENTRIES + 10):
        record_query("CORN", 2024, None, i, hist_dir)
    entries = load_history(hist_dir)
    assert len(entries) == MAX_ENTRIES
    assert entries[-1]["result_count"] == MAX_ENTRIES + 9


def test_clear_history(hist_dir: Path) -> None:
    record_query("CORN", 2024, None, 3, hist_dir)
    clear_history(hist_dir)
    assert load_history(hist_dir) == []


def test_clear_history_no_file(hist_dir: Path) -> None:
    """clear_history should not raise when no history file exists."""
    clear_history(hist_dir)  # should not raise


def test_load_history_bad_json(hist_dir: Path) -> None:
    hist_dir.mkdir(parents=True, exist_ok=True)
    (hist_dir / "history.json").write_text("not json")
    assert load_history(hist_dir) == []
