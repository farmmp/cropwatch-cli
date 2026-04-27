"""Tests for cropwatch.kurtosis."""

import pytest
from cropwatch.kurtosis import (
    KurtosisError,
    KurtosisResult,
    _mean,
    _std,
    _kurt,
    compute_kurtosis,
    format_kurtosis,
)


def _rec(value, week="2024-05-01", commodity="CORN", state="US"):
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "week_ending": week,
        "Value": str(value),
    }


# --- unit helpers ---

def test_mean_basic():
    assert _mean([1.0, 2.0, 3.0, 4.0]) == pytest.approx(2.5)


def test_std_basic():
    mu = _mean([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    sigma = _std([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0], mu)
    assert sigma == pytest.approx(2.0)


def test_kurt_uniform_zero_std_raises():
    with pytest.raises(KurtosisError, match="zero"):
        _kurt([5.0, 5.0, 5.0, 5.0], 5.0, 0.0)


def test_kurt_normal_approx_zero():
    # For a large uniform spread the excess kurtosis should be near -1.2
    vals = [float(i) for i in range(1, 7)]
    mu = _mean(vals)
    sigma = _std(vals, mu)
    k = _kurt(vals, mu, sigma)
    assert k < 0  # platykurtic


# --- compute_kurtosis ---

def test_compute_basic_returns_result():
    records = [_rec(v) for v in [10, 20, 30, 40, 50, 60, 70, 80]]
    result = compute_kurtosis(records, commodity="CORN", state="US")
    assert isinstance(result, KurtosisResult)
    assert result.n == 8


def test_compute_empty_raises():
    with pytest.raises(KurtosisError, match="No records"):
        compute_kurtosis([], commodity="CORN")


def test_compute_too_few_points_raises():
    records = [_rec(v) for v in [10, 20, 30]]
    with pytest.raises(KurtosisError, match="at least 4"):
        compute_kurtosis(records, commodity="CORN", state="US")


def test_compute_filters_commodity():
    records = [_rec(v, commodity="SOYBEANS") for v in range(10)]
    with pytest.raises(KurtosisError):
        compute_kurtosis(records, commodity="CORN", state="US")


def test_compute_filters_state():
    records = [_rec(v, state="IA") for v in range(10)]
    with pytest.raises(KurtosisError):
        compute_kurtosis(records, commodity="CORN", state="US")


def test_compute_skips_bad_values():
    records = [_rec(v) for v in [10, 20, 30, 40]]
    records.append({"commodity_desc": "CORN", "state_alpha": "US", "week_ending": "2024-05-01", "Value": "(D)"})
    result = compute_kurtosis(records, commodity="CORN", state="US")
    assert result.n == 4


def test_compute_leptokurtic_label():
    # Highly peaked distribution (most values same, one outlier)
    vals = [50.0] * 10 + [0.0, 100.0]
    records = [_rec(v) for v in vals]
    result = compute_kurtosis(records, commodity="CORN", state="US")
    assert result.label == "leptokurtic"


def test_compute_platykurtic_label():
    vals = [float(i) for i in range(1, 13)]  # uniform → platykurtic
    records = [_rec(v) for v in vals]
    result = compute_kurtosis(records, commodity="CORN", state="US")
    assert result.label == "platykurtic"


# --- format_kurtosis ---

def test_format_contains_commodity():
    records = [_rec(v) for v in [10, 20, 30, 40, 50, 60]]
    result = compute_kurtosis(records, commodity="CORN", state="US")
    output = format_kurtosis(result)
    assert "CORN" in output


def test_format_contains_label():
    records = [_rec(v) for v in [10, 20, 30, 40, 50, 60]]
    result = compute_kurtosis(records, commodity="CORN", state="US")
    output = format_kurtosis(result)
    assert result.label in output


def test_format_contains_kurtosis_value():
    records = [_rec(v) for v in [10, 20, 30, 40, 50, 60]]
    result = compute_kurtosis(records, commodity="CORN", state="US")
    output = format_kurtosis(result)
    assert str(abs(result.kurtosis))[:4] in output
