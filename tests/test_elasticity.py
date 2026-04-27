"""Tests for cropwatch.elasticity."""
import pytest
from cropwatch.elasticity import (
    ElasticityError,
    ElasticityResult,
    _extract_sorted,
    compute_elasticity,
    format_elasticity,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "US") -> dict:
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "week_ending": week,
        "Value": str(value),
    }


_BASE = [
    _rec("2023-04-01", 10.0),
    _rec("2023-04-08", 20.0),
    _rec("2023-04-15", 15.0),
    _rec("2023-04-22", 30.0),
]


def test_extract_sorted_basic():
    pairs = _extract_sorted(_BASE, "CORN", "US")
    assert len(pairs) == 4
    assert pairs[0] == ("2023-04-01", 10.0)


def test_extract_sorted_filters_commodity():
    records = _BASE + [_rec("2023-04-01", 99.0, commodity="SOYBEANS")]
    pairs = _extract_sorted(records, "CORN", "US")
    assert all(v != 99.0 for _, v in pairs)


def test_extract_sorted_filters_state():
    records = _BASE + [_rec("2023-04-01", 99.0, state="IA")]
    pairs = _extract_sorted(records, "CORN", "US")
    assert len(pairs) == 4


def test_extract_sorted_skips_bad_value():
    bad = {"commodity_desc": "CORN", "state_alpha": "US", "week_ending": "2023-04-01", "Value": "N/A"}
    pairs = _extract_sorted([bad], "CORN", "US")
    assert pairs == []


def test_compute_basic_length():
    result = compute_elasticity(_BASE, "CORN", "US")
    assert len(result.elasticities) == len(_BASE) - 1


def test_compute_basic_values():
    result = compute_elasticity(_BASE, "CORN", "US")
    # 10 -> 20 = +100%
    assert result.elasticities[0] == pytest.approx(100.0)
    # 20 -> 15 = -25%
    assert result.elasticities[1] == pytest.approx(-25.0)


def test_compute_mean_elasticity():
    result = compute_elasticity(_BASE, "CORN", "US")
    expected_mean = sum(result.elasticities) / len(result.elasticities)
    assert result.mean_elasticity == pytest.approx(expected_mean, rel=1e-4)


def test_compute_max_min():
    result = compute_elasticity(_BASE, "CORN", "US")
    assert result.max_elasticity == max(result.elasticities)
    assert result.min_elasticity == min(result.elasticities)


def test_compute_zero_prev_value():
    records = [_rec("2023-04-01", 0.0), _rec("2023-04-08", 50.0)]
    result = compute_elasticity(records, "CORN", "US")
    assert result.elasticities[0] == 0.0


def test_compute_empty_raises():
    with pytest.raises(ElasticityError, match="No records"):
        compute_elasticity([], "CORN", "US")


def test_compute_too_few_points_raises():
    with pytest.raises(ElasticityError, match="at least 2"):
        compute_elasticity([_rec("2023-04-01", 10.0)], "CORN", "US")


def test_format_contains_header():
    result = compute_elasticity(_BASE, "CORN", "US")
    out = format_elasticity(result)
    assert "Elasticity" in out
    assert "CORN" in out
    assert "US" in out


def test_format_contains_mean():
    result = compute_elasticity(_BASE, "CORN", "US")
    out = format_elasticity(result)
    assert "Mean" in out


def test_format_row_count():
    result = compute_elasticity(_BASE, "CORN", "US")
    out = format_elasticity(result)
    # One row per week
    for week in result.week_endings:
        assert week in out
