"""Tests for cropwatch.percentile."""
import pytest
from cropwatch.percentile import compute_percentiles, format_percentiles, PercentileError


def _rec(state, value, commodity="corn", week="2024-06-02"):
    return {
        "state_alpha": state,
        "commodity_desc": commodity,
        "week_ending": week,
        "Value": str(value),
    }


SAMPLE = [
    _rec("IA", 80),
    _rec("IL", 60),
    _rec("MN", 40),
    _rec("NE", 20),
    _rec("US", 55),  # should be excluded
]


def test_compute_basic():
    results = compute_percentiles(SAMPLE, commodity="corn", week_ending="2024-06-02")
    assert len(results) == 4
    states = [r.state_desc for r in results]
    assert "US" not in states


def test_compute_sorted_descending():
    results = compute_percentiles(SAMPLE, commodity="corn", week_ending="2024-06-02")
    values = [r.value for r in results]
    assert values == sorted(values, reverse=True)


def test_compute_percentile_range():
    results = compute_percentiles(SAMPLE, commodity="corn", week_ending="2024-06-02")
    for r in results:
        assert 0.0 <= r.percentile <= 100.0


def test_empty_records_raises():
    with pytest.raises(PercentileError, match="No records"):
        compute_percentiles([], commodity="corn", week_ending="2024-06-02")


def test_no_matching_week_raises():
    with pytest.raises(PercentileError):
        compute_percentiles(SAMPLE, commodity="corn", week_ending="1999-01-01")


def test_no_matching_commodity_raises():
    with pytest.raises(PercentileError):
        compute_percentiles(SAMPLE, commodity="soybeans", week_ending="2024-06-02")


def test_skips_non_numeric():
    bad = SAMPLE + [_rec("KS", "N/A")]
    results = compute_percentiles(bad, commodity="corn", week_ending="2024-06-02")
    states = [r.state_desc for r in results]
    assert "KS" not in states


def test_single_state_percentile_100():
    records = [_rec("IA", 75)]
    results = compute_percentiles(records, commodity="corn", week_ending="2024-06-02")
    assert len(results) == 1
    assert results[0].percentile == 100.0


def test_format_contains_header():
    results = compute_percentiles(SAMPLE, commodity="corn", week_ending="2024-06-02")
    output = format_percentiles(results, commodity="corn", week_ending="2024-06-02")
    assert "Percentile Ranking" in output
    assert "2024-06-02" in output
    assert "State" in output
