"""Unit tests for cropwatch.leadlag."""
from __future__ import annotations

import pytest

from cropwatch.leadlag import (
    LeadLagError,
    LeadLagResult,
    _extract_sorted,
    _pearson,
    compute_leadlag,
    format_leadlag,
)


def _rec(commodity: str, week: str, value: float, state: str = "US") -> dict:
    return {
        "commodity_desc": commodity,
        "week_ending": week,
        "Value": str(value),
        "state_alpha": state,
    }


CORN = "CORN"
SOY = "SOYBEANS"


def _base_records():
    weeks = [f"2023-0{i}-01" for i in range(1, 9)]
    corn_vals = [10, 20, 30, 40, 50, 60, 70, 80]
    soy_vals = [5, 10, 20, 30, 40, 50, 60, 70]  # soy lags corn by 1 week
    records = []
    for w, cv, sv in zip(weeks, corn_vals, soy_vals):
        records.append(_rec(CORN, w, cv))
        records.append(_rec(SOY, w, sv))
    return records


# --- _extract_sorted ---

def test_extract_sorted_basic():
    records = [_rec(CORN, "2023-03-01", 30), _rec(CORN, "2023-01-01", 10), _rec(CORN, "2023-02-01", 20)]
    result = _extract_sorted(records, CORN, None)
    assert result == [10.0, 20.0, 30.0]


def test_extract_sorted_filters_commodity():
    records = [_rec(CORN, "2023-01-01", 10), _rec(SOY, "2023-01-01", 99)]
    result = _extract_sorted(records, CORN, None)
    assert result == [10.0]


def test_extract_sorted_filters_state():
    records = [_rec(CORN, "2023-01-01", 10, "IA"), _rec(CORN, "2023-01-01", 99, "IL")]
    result = _extract_sorted(records, CORN, "IA")
    assert result == [10.0]


def test_extract_sorted_skips_bad_value():
    records = [_rec(CORN, "2023-01-01", 10), {"commodity_desc": CORN, "week_ending": "2023-02-01", "Value": "N/A", "state_alpha": "US"}]
    result = _extract_sorted(records, CORN, None)
    assert result == [10.0]


# --- _pearson ---

def test_pearson_perfect_positive():
    a = [1.0, 2.0, 3.0, 4.0]
    b = [2.0, 4.0, 6.0, 8.0]
    assert abs(_pearson(a, b) - 1.0) < 1e-9


def test_pearson_perfect_negative():
    a = [1.0, 2.0, 3.0]
    b = [3.0, 2.0, 1.0]
    assert abs(_pearson(a, b) + 1.0) < 1e-9


def test_pearson_empty():
    assert _pearson([], []) == 0.0


# --- compute_leadlag ---

def test_compute_leadlag_basic():
    records = _base_records()
    result = compute_leadlag(records, CORN, SOY, max_lag=3)
    assert isinstance(result, LeadLagResult)
    assert result.commodity_a == CORN
    assert result.commodity_b == SOY


def test_compute_leadlag_detects_lag():
    records = _base_records()
    result = compute_leadlag(records, CORN, SOY, max_lag=3)
    # corn leads soy by 1 week in our fixture
    assert result.best_lag == 1
    assert result.correlation > 0.9


def test_compute_leadlag_empty_raises():
    with pytest.raises(LeadLagError, match="No records"):
        compute_leadlag([], CORN, SOY)


def test_compute_leadlag_insufficient_data_raises():
    records = [_rec(CORN, "2023-01-01", 10)]
    with pytest.raises(LeadLagError):
        compute_leadlag(records, CORN, SOY)


# --- format_leadlag ---

def test_format_leadlag_leads():
    result = LeadLagResult(commodity_a=CORN, commodity_b=SOY, best_lag=2, correlation=0.95, max_lag=4)
    text = format_leadlag(result)
    assert "leads" in text
    assert "2" in text
    assert "0.9500" in text


def test_format_leadlag_lags():
    result = LeadLagResult(commodity_a=CORN, commodity_b=SOY, best_lag=-1, correlation=0.88, max_lag=4)
    text = format_leadlag(result)
    assert f"{SOY} leads {CORN}" in text


def test_format_leadlag_in_phase():
    result = LeadLagResult(commodity_a=CORN, commodity_b=SOY, best_lag=0, correlation=0.99, max_lag=4)
    text = format_leadlag(result)
    assert "in-phase" in text
