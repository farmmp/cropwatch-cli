"""Tests for cropwatch.moving_avg."""
import pytest
from cropwatch.moving_avg import (
    compute_moving_avg,
    format_moving_avg,
    MovingAvgError,
    MovingAvgResult,
)


def _rec(week, value, commodity="CORN", attr="PROGRESS", state=None):
    r = {
        "commodity_desc": commodity,
        "statisticcat_desc": attr,
        "unit_desc": "PCT",
        "week_ending": week,
        "Value": str(value),
    }
    if state:
        r["state_alpha"] = state
    return r


def test_compute_basic():
    records = [_rec(f"2024-0{i}-01", i * 10) for i in range(1, 6)]
    results = compute_moving_avg(records, "CORN", "PROGRESS", window=2)
    assert len(results) == 5
    assert all(isinstance(r, MovingAvgResult) for r in results)


def test_compute_window1_deviation_zero():
    records = [_rec("2024-01-01", 50)]
    results = compute_moving_avg(records, "CORN", "PROGRESS", window=1)
    assert results[0].deviation == 0.0


def test_compute_window_larger_than_series():
    records = [_rec(f"2024-0{i}-01", float(i * 10)) for i in range(1, 4)]
    results = compute_moving_avg(records, "CORN", "PROGRESS", window=10)
    assert len(results) == 3
    # last avg should be mean of all three
    assert results[-1].avg == pytest.approx(20.0)


def test_compute_filters_state():
    records = [
        _rec("2024-01-01", 40, state="IA"),
        _rec("2024-01-01", 80, state="IL"),
    ]
    results = compute_moving_avg(records, "CORN", "PROGRESS", window=1, state="IA")
    assert len(results) == 1
    assert results[0].value == 40.0


def test_empty_records_raises():
    with pytest.raises(MovingAvgError, match="No records"):
        compute_moving_avg([], "CORN", "PROGRESS")


def test_no_matching_raises():
    records = [_rec("2024-01-01", 50, commodity="WHEAT")]
    with pytest.raises(MovingAvgError, match="No data"):
        compute_moving_avg(records, "CORN", "PROGRESS")


def test_bad_window_raises():
    records = [_rec("2024-01-01", 50)]
    with pytest.raises(MovingAvgError, match="Window"):
        compute_moving_avg(records, "CORN", "PROGRESS", window=0)


def test_format_contains_header():
    records = [_rec("2024-01-01", 50)]
    results = compute_moving_avg(records, "CORN", "PROGRESS")
    out = format_moving_avg(results)
    assert "Week" in out
    assert "Dev" in out


def test_format_row_count():
    records = [_rec(f"2024-0{i}-01", i * 10) for i in range(1, 5)]
    results = compute_moving_avg(records, "CORN", "PROGRESS")
    lines = format_moving_avg(results).splitlines()
    # header + sep + 4 data rows
    assert len(lines) == 6
