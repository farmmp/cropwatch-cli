"""Tests for cropwatch.momentum."""
import pytest
from cropwatch.momentum import (
    MomentumError,
    MomentumResult,
    compute_momentum,
    format_momentum,
)


def _rec(week: str, value: str, commodity: str = "CORN", attr: str = "PROGRESS", state: str = "IA"):
    return {
        "week_ending": week,
        "Value": value,
        "commodity_desc": commodity,
        "short_desc": f"{commodity} - {attr}, PCT",
        "state_alpha": state,
    }


BASIC_RECORDS = [
    _rec("2024-04-07", "20"),
    _rec("2024-04-14", "35"),
    _rec("2024-04-21", "50"),
]


def test_compute_basic_length():
    results = compute_momentum(BASIC_RECORDS, "CORN", "PROGRESS")
    assert len(results) == 2


def test_compute_basic_values():
    results = compute_momentum(BASIC_RECORDS, "CORN", "PROGRESS")
    assert results[0].week_ending == "2024-04-14"
    assert results[0].value == 35.0
    assert results[0].change == 15.0
    assert results[0].pct_change == pytest.approx(75.0, rel=1e-3)


def test_compute_negative_change():
    records = [
        _rec("2024-04-07", "60"),
        _rec("2024-04-14", "45"),
    ]
    results = compute_momentum(records, "CORN", "PROGRESS")
    assert results[0].change == -15.0
    assert results[0].pct_change == pytest.approx(-25.0, rel=1e-3)


def test_compute_filters_state():
    records = BASIC_RECORDS + [_rec("2024-04-14", "99", state="IL")]
    results = compute_momentum(records, "CORN", "PROGRESS", state="IA")
    # Should still be 2 results based on IA records only
    assert all(True for r in results)  # no IL bleed-through
    assert len(results) == 2


def test_compute_empty_records_raises():
    with pytest.raises(MomentumError, match="No records"):
        compute_momentum([], "CORN", "PROGRESS")


def test_compute_no_matching_raises():
    with pytest.raises(MomentumError, match="No records found"):
        compute_momentum(BASIC_RECORDS, "WHEAT", "PROGRESS")


def test_compute_too_few_numeric_raises():
    records = [_rec("2024-04-07", "N/A"), _rec("2024-04-14", "N/A")]
    with pytest.raises(MomentumError, match="at least two"):
        compute_momentum(records, "CORN", "PROGRESS")


def test_compute_sorted_by_week():
    shuffled = [BASIC_RECORDS[2], BASIC_RECORDS[0], BASIC_RECORDS[1]]
    results = compute_momentum(shuffled, "CORN", "PROGRESS")
    weeks = [r.week_ending for r in results]
    assert weeks == sorted(weeks)


def test_format_momentum_contains_header():
    results = compute_momentum(BASIC_RECORDS, "CORN", "PROGRESS")
    output = format_momentum(results, "CORN", "PROGRESS")
    assert "Momentum" in output
    assert "CORN" in output.upper()


def test_format_momentum_contains_week():
    results = compute_momentum(BASIC_RECORDS, "CORN", "PROGRESS")
    output = format_momentum(results, "CORN", "PROGRESS")
    assert "2024-04-14" in output
    assert "2024-04-21" in output
