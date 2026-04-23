"""Unit tests for cropwatch.volatility."""
from __future__ import annotations

import pytest

from cropwatch.volatility import (
    VolatilityError,
    VolatilityResult,
    _week_changes,
    compute_volatility,
    format_volatility,
)


def _rec(value: float, week: str = "2023-04-01", state: str = "US") -> dict:
    return {
        "commodity_desc": "CORN",
        "short_desc": "CORN - PROGRESS, MEASURED IN PCT PLANTED",
        "state_alpha": state,
        "year": 2023,
        "week_ending": week,
        "Value": str(value),
    }


RECORDS = [
    _rec(10.0, "2023-04-01"),
    _rec(20.0, "2023-04-08"),
    _rec(35.0, "2023-04-15"),
    _rec(50.0, "2023-04-22"),
    _rec(60.0, "2023-04-29"),
]


def test_week_changes_basic():
    changes = _week_changes(RECORDS, "CORN", "PCT PLANTED", None)
    assert changes == [10.0, 15.0, 15.0, 10.0]


def test_week_changes_too_few_points():
    with pytest.raises(VolatilityError, match="at least 2"):
        _week_changes([_rec(5.0)], "CORN", "PCT PLANTED", None)


def test_week_changes_empty():
    with pytest.raises(VolatilityError):
        _week_changes([], "CORN", "PCT PLANTED", None)


def test_compute_volatility_basic():
    result = compute_volatility(RECORDS, "CORN", "PCT PLANTED")
    assert isinstance(result, VolatilityResult)
    assert result.weeks == 5
    assert result.mean_change == pytest.approx(12.5, abs=0.01)
    assert result.min_change == 10.0
    assert result.max_change == 15.0
    assert result.std_dev >= 0


def test_compute_volatility_state_filter():
    state_records = [
        _rec(5.0, "2023-04-01", "IA"),
        _rec(15.0, "2023-04-08", "IA"),
        _rec(10.0, "2023-04-01", "IL"),
        _rec(30.0, "2023-04-08", "IL"),
    ]
    result_ia = compute_volatility(state_records, "CORN", "PCT PLANTED", state="IA")
    assert result_ia.mean_change == pytest.approx(10.0)
    result_il = compute_volatility(state_records, "CORN", "PCT PLANTED", state="IL")
    assert result_il.mean_change == pytest.approx(20.0)


def test_compute_volatility_skips_bad_values():
    records = [
        _rec(10.0, "2023-04-01"),
        {"commodity_desc": "CORN", "short_desc": "CORN - PROGRESS, MEASURED IN PCT PLANTED",
         "state_alpha": "US", "year": 2023, "week_ending": "2023-04-08", "Value": "(D)"},
        _rec(30.0, "2023-04-15"),
    ]
    result = compute_volatility(records, "CORN", "PCT PLANTED")
    assert result.weeks == 2  # only two numeric values


def test_format_volatility_contains_key_info():
    result = compute_volatility(RECORDS, "CORN", "PCT PLANTED")
    output = format_volatility(result)
    assert "CORN" in output
    assert "Std-dev" in output
    assert "Weeks" in output
    assert "Mean" in output
