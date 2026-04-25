"""Tests for cropwatch.cyclical."""
import math
import pytest
from cropwatch.cyclical import (
    CyclicalError,
    CyclicalResult,
    _autocorrelation,
    _extract_sorted,
    detect_cyclical,
    format_cyclical,
)


def _rec(week: str, value: float, commodity: str = "Corn", state: str = "US") -> dict:
    return {
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": commodity,
        "state_alpha": state,
    }


# --- _extract_sorted ---

def test_extract_sorted_basic():
    records = [_rec("2023-06-01", 50.0), _rec("2023-05-01", 40.0)]
    result = _extract_sorted(records, "Corn", "US")
    assert result[0][0] == "2023-05-01"
    assert result[1][0] == "2023-06-01"


def test_extract_sorted_filters_commodity():
    records = [_rec("2023-06-01", 50.0, "Corn"), _rec("2023-06-01", 60.0, "Soybeans")]
    result = _extract_sorted(records, "Corn", "US")
    assert len(result) == 1


def test_extract_sorted_filters_state():
    records = [_rec("2023-06-01", 50.0, "Corn", "US"), _rec("2023-06-01", 60.0, "Corn", "IA")]
    result = _extract_sorted(records, "Corn", "IA")
    assert len(result) == 1
    assert result[0][1] == 60.0


def test_extract_sorted_skips_bad_value():
    records = [_rec("2023-06-01", 50.0), {"week_ending": "2023-07-01", "Value": "N/A", "commodity_desc": "Corn", "state_alpha": "US"}]
    result = _extract_sorted(records, "Corn", "US")
    assert len(result) == 1


# --- _autocorrelation ---

def test_autocorrelation_uniform_returns_zero():
    values = [5.0, 5.0, 5.0, 5.0, 5.0]
    assert _autocorrelation(values, 1) == 0.0


def test_autocorrelation_lag_too_large():
    values = [1.0, 2.0, 3.0]
    assert _autocorrelation(values, 10) == 0.0


def test_autocorrelation_positive_for_repeating():
    # Perfectly repeating pattern with period 2
    values = [0.0, 10.0] * 6
    ac = _autocorrelation(values, 2)
    assert ac > 0.5


# --- detect_cyclical ---

def test_detect_too_few_raises():
    records = [_rec(f"2023-0{i}-01", float(i)) for i in range(1, 4)]
    with pytest.raises(CyclicalError):
        detect_cyclical(records, "Corn", "US")


def test_detect_returns_result():
    records = [_rec(f"2023-{i:02d}-01", float(i % 5)) for i in range(1, 13)]
    result = detect_cyclical(records, "Corn", "US")
    assert isinstance(result, CyclicalResult)
    assert result.commodity == "Corn"
    assert result.state == "US"
    assert 1 <= result.period_weeks <= 12


def test_detect_period_for_sine_like():
    import math
    records = [
        _rec(f"2023-{i:02d}-01", round(50 + 30 * math.sin(2 * math.pi * i / 6), 2))
        for i in range(1, 25)
    ]
    result = detect_cyclical(records, "Corn", "US", max_period=12)
    # Period 6 should have high autocorrelation
    assert result.period_weeks == 6


def test_detect_identifies_peaks_and_troughs():
    # Alternating high-low pattern
    values = [10.0, 90.0, 10.0, 90.0, 10.0, 90.0, 10.0, 90.0]
    records = [_rec(f"2023-{i:02d}-01", v) for i, v in enumerate(values, 1)]
    result = detect_cyclical(records, "Corn", "US")
    assert len(result.peak_weeks) > 0
    assert len(result.trough_weeks) > 0


# --- format_cyclical ---

def test_format_contains_commodity():
    records = [_rec(f"2023-{i:02d}-01", float(i)) for i in range(1, 13)]
    result = detect_cyclical(records, "Corn", "US")
    text = format_cyclical(result)
    assert "Corn" in text
    assert "US" in text
    assert "Dominant period" in text
    assert "Autocorrelation" in text
