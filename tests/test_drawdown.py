"""Tests for cropwatch.drawdown."""
from __future__ import annotations

import pytest

from cropwatch.drawdown import (
    DrawdownError,
    DrawdownResult,
    _extract_sorted,
    compute_drawdown,
    format_drawdown,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "US") -> dict:
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "statisticcat_desc": "PROGRESS",
        "week_ending": week,
        "Value": str(value),
    }


# ---------------------------------------------------------------------------
# _extract_sorted
# ---------------------------------------------------------------------------

def test_extract_sorted_basic():
    records = [_rec("2023-06-04", 40.0), _rec("2023-05-28", 30.0)]
    series = _extract_sorted(records, "CORN", "US", "PROGRESS")
    assert series == [(20230528, 30.0), (20230604, 40.0)]


def test_extract_sorted_filters_commodity():
    records = [_rec("2023-05-28", 30.0, commodity="SOYBEANS")]
    series = _extract_sorted(records, "CORN", "US", "PROGRESS")
    assert series == []


def test_extract_sorted_filters_state():
    records = [_rec("2023-05-28", 30.0, state="IA"), _rec("2023-05-28", 40.0, state="IL")]
    series = _extract_sorted(records, "CORN", "IA", "PROGRESS")
    assert len(series) == 1
    assert series[0][1] == 30.0


def test_extract_sorted_skips_bad_value():
    records = [_rec("2023-05-28", 30.0), {"commodity_desc": "CORN", "state_alpha": "US",
                                           "statisticcat_desc": "PROGRESS",
                                           "week_ending": "2023-06-04", "Value": "(D)"}]
    series = _extract_sorted(records, "CORN", "US", "PROGRESS")
    assert len(series) == 1


# ---------------------------------------------------------------------------
# compute_drawdown
# ---------------------------------------------------------------------------

def test_compute_drawdown_basic():
    records = [
        _rec("2023-05-07", 10.0),
        _rec("2023-05-14", 50.0),
        _rec("2023-05-21", 20.0),
        _rec("2023-05-28", 60.0),
    ]
    result = compute_drawdown(records, "CORN")
    assert isinstance(result, DrawdownResult)
    assert result.drawdown == pytest.approx(30.0)
    assert result.peak_value == pytest.approx(50.0)
    assert result.trough_value == pytest.approx(20.0)


def test_compute_drawdown_monotonic_increase():
    records = [_rec(f"2023-05-0{i}", float(i * 10)) for i in range(1, 6)]
    result = compute_drawdown(records, "CORN")
    assert result.drawdown == pytest.approx(0.0)


def test_compute_drawdown_empty_raises():
    with pytest.raises(DrawdownError, match="No records"):
        compute_drawdown([], "CORN")


def test_compute_drawdown_too_few_points_raises():
    records = [_rec("2023-05-07", 40.0)]
    with pytest.raises(DrawdownError, match="Not enough"):
        compute_drawdown(records, "CORN")


def test_compute_drawdown_largest_selected():
    """Ensure the *maximum* drawdown is returned when multiple troughs exist."""
    records = [
        _rec("2023-05-07", 10.0),
        _rec("2023-05-14", 40.0),
        _rec("2023-05-21", 35.0),  # drawdown 5
        _rec("2023-05-28", 80.0),
        _rec("2023-06-04", 20.0),  # drawdown 60 ← largest
    ]
    result = compute_drawdown(records, "CORN")
    assert result.drawdown == pytest.approx(60.0)
    assert result.peak_value == pytest.approx(80.0)
    assert result.trough_value == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# format_drawdown
# ---------------------------------------------------------------------------

def test_format_drawdown_contains_key_info():
    result = DrawdownResult(
        commodity="CORN",
        state="US",
        peak_week=20230514,
        peak_value=80.0,
        trough_week=20230604,
        trough_value=20.0,
        drawdown=60.0,
    )
    output = format_drawdown(result)
    assert "CORN" in output
    assert "80.0" in output
    assert "20.0" in output
    assert "60.0" in output
    assert "Drawdown" in output
