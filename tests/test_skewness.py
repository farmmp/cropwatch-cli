"""Tests for cropwatch.skewness."""
from __future__ import annotations

import pytest

from cropwatch.skewness import (
    SkewnessError,
    SkewnessResult,
    _mean,
    _std,
    _skew,
    compute_skewness,
    format_skewness,
)


def _rec(value, state="IA", commodity="CORN", week="2023-06-04"):
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "Value": str(value),
        "week_ending": week,
    }


# --- unit helpers ---

def test_mean_basic():
    assert _mean([1.0, 2.0, 3.0]) == pytest.approx(2.0)


def test_std_basic():
    assert _std([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0], 5.0) == pytest.approx(2.0)


def test_skew_too_few_raises():
    with pytest.raises(SkewnessError, match="At least 3"):
        _skew([1.0, 2.0])


def test_skew_uniform_is_zero():
    assert _skew([5.0, 5.0, 5.0, 5.0]) == pytest.approx(0.0)


def test_skew_right_skewed():
    # A right-skewed distribution
    values = [1.0, 1.0, 1.0, 1.0, 1.0, 10.0]
    assert _skew(values) > 0.5


def test_skew_left_skewed():
    values = [10.0, 10.0, 10.0, 10.0, 10.0, 1.0]
    assert _skew(values) < -0.5


# --- compute_skewness ---

def test_compute_basic_returns_result():
    records = [_rec(v) for v in [40, 45, 50, 55, 60, 65]]
    result = compute_skewness(records, commodity="CORN", state="IA")
    assert isinstance(result, SkewnessResult)
    assert result.n == 6
    assert result.commodity == "CORN"
    assert result.state == "IA"


def test_compute_empty_raises():
    with pytest.raises(SkewnessError, match="No records"):
        compute_skewness([], commodity="CORN")


def test_compute_too_few_raises():
    records = [_rec(50), _rec(60)]
    with pytest.raises(SkewnessError, match="Not enough"):
        compute_skewness(records, commodity="CORN", state="IA")


def test_compute_skips_non_numeric():
    records = [_rec(v) for v in [40, 50, 60]] + [
        {"commodity_desc": "CORN", "state_alpha": "IA", "Value": "N/A", "week_ending": "2023-06-04"}
    ]
    result = compute_skewness(records, commodity="CORN", state="IA")
    assert result.n == 3


def test_compute_filters_state():
    records = [_rec(v, state="IA") for v in [40, 50, 60]] + \
              [_rec(v, state="IL") for v in [10, 90, 50]]
    result = compute_skewness(records, commodity="CORN", state="IA")
    assert result.n == 3


def test_compute_no_state_uses_all():
    records = [_rec(v, state="IA") for v in [40, 50, 60]] + \
              [_rec(v, state="IL") for v in [40, 50, 60]]
    result = compute_skewness(records, commodity="CORN")
    assert result.n == 6
    assert result.state is None


def test_compute_interpretation_symmetric():
    records = [_rec(v) for v in [49, 50, 51, 50, 49, 51]]
    result = compute_skewness(records, commodity="CORN", state="IA")
    assert "symmetric" in result.interpretation


# --- format_skewness ---

def test_format_contains_commodity():
    records = [_rec(v) for v in [40, 50, 60, 55, 45, 48]]
    result = compute_skewness(records, commodity="CORN", state="IA")
    output = format_skewness(result)
    assert "CORN" in output


def test_format_contains_skewness_value():
    records = [_rec(v) for v in [40, 50, 60, 55, 45, 48]]
    result = compute_skewness(records, commodity="CORN", state="IA")
    output = format_skewness(result)
    assert "Skewness" in output


def test_format_no_state_shows_us():
    records = [_rec(v, state="IA") for v in [40, 50, 60]] + \
              [_rec(v, state="IL") for v in [40, 50, 60]]
    result = compute_skewness(records, commodity="CORN")
    output = format_skewness(result)
    assert "US" in output
