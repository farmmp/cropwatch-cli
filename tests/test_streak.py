"""Tests for cropwatch.streak."""
from __future__ import annotations

import pytest

from cropwatch.streak import (
    StreakError,
    StreakResult,
    detect_streak,
    format_streak,
    _extract_sorted,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "US") -> dict:
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "week_ending": week,
        "Value": str(value),
    }


records_up = [
    _rec("2023-04-01", 10.0),
    _rec("2023-04-08", 20.0),
    _rec("2023-04-15", 30.0),
    _rec("2023-04-22", 25.0),
    _rec("2023-04-29", 35.0),
]


def test_extract_sorted_basic():
    result = _extract_sorted(records_up, "CORN", None)
    assert len(result) == 5
    assert result[0][0] < result[-1][0]


def test_extract_sorted_filters_commodity():
    mixed = records_up + [_rec("2023-04-01", 5.0, commodity="SOYBEANS")]
    result = _extract_sorted(mixed, "CORN", None)
    assert len(result) == 5


def test_detect_streak_up():
    result = detect_streak(records_up, "CORN")
    assert isinstance(result, StreakResult)
    assert result.direction == "up"
    assert result.length == 3
    assert result.start_value == 10.0
    assert result.end_value == 30.0


def test_detect_streak_down():
    records = [
        _rec("2023-04-01", 50.0),
        _rec("2023-04-08", 40.0),
        _rec("2023-04-15", 30.0),
        _rec("2023-04-22", 20.0),
        _rec("2023-04-29", 25.0),
    ]
    result = detect_streak(records, "CORN")
    assert result.direction == "down"
    assert result.length == 4


def test_detect_streak_with_state():
    state_records = [_rec(w, v, state="IA") for w, v in [
        ("2023-04-01", 10.0), ("2023-04-08", 20.0), ("2023-04-15", 30.0)
    ]]
    result = detect_streak(state_records, "CORN", state="IA")
    assert result.state == "IA"
    assert result.length == 3


def test_detect_streak_empty_raises():
    with pytest.raises(StreakError, match="No records"):
        detect_streak([], "CORN")


def test_detect_streak_too_few_raises():
    with pytest.raises(StreakError, match="Not enough"):
        detect_streak([_rec("2023-04-01", 10.0)], "CORN")


def test_detect_streak_flat_raises():
    flat = [_rec(f"2023-04-{d:02d}", 50.0) for d in [1, 8, 15]]
    with pytest.raises(StreakError, match="No directional"):
        detect_streak(flat, "CORN")


def test_format_streak_contains_key_info():
    result = StreakResult(
        commodity="CORN",
        state=None,
        direction="up",
        length=4,
        start_week=20230401,
        end_week=20230422,
        start_value=10.0,
        end_value=40.0,
    )
    output = format_streak(result)
    assert "CORN" in output
    assert "up" in output.lower()
    assert "4 weeks" in output
    assert "10.0" in output
    assert "40.0" in output
