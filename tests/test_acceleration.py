"""Tests for cropwatch.acceleration."""
import pytest
from cropwatch.acceleration import (
    AccelerationError,
    AccelerationResult,
    _extract_sorted,
    compute_acceleration,
    format_acceleration,
)


def _rec(week: str, value, commodity: str = "CORN", state: str = "IA") -> dict:
    return {
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": commodity,
        "state_alpha": state,
    }


BASE_RECORDS = [
    _rec("2024-04-07", 10),
    _rec("2024-04-14", 20),
    _rec("2024-04-21", 35),
    _rec("2024-04-28", 45),
    _rec("2024-05-05", 50),
]


def test_extract_sorted_basic():
    result = _extract_sorted(BASE_RECORDS, "CORN")
    assert [w for w, _ in result] == [
        "2024-04-07",
        "2024-04-14",
        "2024-04-21",
        "2024-04-28",
        "2024-05-05",
    ]


def test_extract_sorted_filters_commodity():
    mixed = BASE_RECORDS + [_rec("2024-04-07", 99, commodity="SOYBEANS")]
    result = _extract_sorted(mixed, "CORN")
    assert all(True for _, v in result if v != 99)
    assert len(result) == 5


def test_extract_sorted_filters_state():
    mixed = BASE_RECORDS + [_rec("2024-04-07", 99, state="IL")]
    result = _extract_sorted(mixed, "CORN", state="IA")
    assert len(result) == 5


def test_extract_sorted_skips_bad_value():
    bad = BASE_RECORDS + [{"week_ending": "2024-05-12", "Value": "N/A",
                           "commodity_desc": "CORN", "state_alpha": "IA"}]
    result = _extract_sorted(bad, "CORN")
    assert len(result) == 5


def test_compute_acceleration_basic_length():
    results = compute_acceleration(BASE_RECORDS, "CORN")
    # n=5 points → n-2=3 acceleration values
    assert len(results) == 3


def test_compute_acceleration_basic_values():
    results = compute_acceleration(BASE_RECORDS, "CORN")
    # week 3 (index 2): first_diff = 35-20=15, prev_first_diff=20-10=10 → accel=5
    assert results[0].first_diff == pytest.approx(15.0)
    assert results[0].acceleration == pytest.approx(5.0)


def test_compute_acceleration_negative():
    records = [
        _rec("2024-04-07", 50),
        _rec("2024-04-14", 40),
        _rec("2024-04-21", 25),
    ]
    results = compute_acceleration(records, "CORN")
    assert results[0].acceleration == pytest.approx(-5.0)


def test_compute_empty_raises():
    with pytest.raises(AccelerationError, match="No data found"):
        compute_acceleration([], "CORN")


def test_compute_too_few_points_raises():
    records = [_rec("2024-04-07", 10), _rec("2024-04-14", 20)]
    with pytest.raises(AccelerationError, match="at least 3"):
        compute_acceleration(records, "CORN")


def test_format_acceleration_contains_header():
    results = compute_acceleration(BASE_RECORDS, "CORN")
    output = format_acceleration(results, "CORN")
    assert "Acceleration" in output
    assert "CORN" in output


def test_format_acceleration_contains_weeks():
    results = compute_acceleration(BASE_RECORDS, "CORN")
    output = format_acceleration(results, "CORN")
    assert "2024-04-21" in output
    assert "2024-04-28" in output
    assert "2024-05-05" in output
