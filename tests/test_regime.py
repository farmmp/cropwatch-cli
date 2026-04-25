"""Unit tests for cropwatch.regime."""
from __future__ import annotations

import pytest

from cropwatch.regime import (
    RegimeError,
    RegimeResult,
    _extract_sorted,
    detect_regimes,
    format_regimes,
)


def _rec(commodity: str, week: str, value: float, state: str = "US") -> dict:
    return {
        "commodity_desc": commodity,
        "week_ending": week,
        "Value": str(value),
        "state_alpha": state,
    }


RECORDS = [
    _rec("CORN", "2023-05-01", 10.0),
    _rec("CORN", "2023-05-08", 20.0),
    _rec("CORN", "2023-05-15", 30.0),
    _rec("CORN", "2023-05-22", 40.0),
    _rec("CORN", "2023-05-29", 50.0),
]


def test_extract_sorted_basic():
    rows = _extract_sorted(RECORDS, "CORN")
    assert len(rows) == 5
    weeks = [r[0] for r in rows]
    assert weeks == sorted(weeks)


def test_extract_sorted_filters_commodity():
    extra = RECORDS + [_rec("SOYBEANS", "2023-05-01", 99.0)]
    rows = _extract_sorted(extra, "CORN")
    assert len(rows) == 5


def test_extract_sorted_filters_state():
    mixed = RECORDS + [_rec("CORN", "2023-05-01", 99.0, state="IA")]
    rows = _extract_sorted(mixed, "CORN", state="IA")
    assert len(rows) == 1
    assert rows[0][1] == 99.0


def test_extract_sorted_skips_bad_value():
    bad = RECORDS + [{"commodity_desc": "CORN", "week_ending": "2023-06-01", "Value": "(D)", "state_alpha": "US"}]
    rows = _extract_sorted(bad, "CORN")
    assert len(rows) == 5


def test_detect_regimes_length():
    results = detect_regimes(RECORDS, commodity="CORN")
    assert len(results) == len(RECORDS)


def test_detect_regimes_labels():
    # mean of 10,20,30,40,50 = 30
    results = detect_regimes(RECORDS, commodity="CORN")
    assert results[0].regime == "below"   # 10 < 30
    assert results[2].regime == "neutral" # 30 == mean => neutral (threshold=0)
    assert results[4].regime == "above"   # 50 > 30


def test_detect_regimes_first_row_never_shift():
    results = detect_regimes(RECORDS, commodity="CORN")
    assert results[0].shift is False


def test_detect_regimes_shift_detected():
    results = detect_regimes(RECORDS, commodity="CORN")
    # Regime should change somewhere across the 5 points
    assert any(r.shift for r in results)


def test_detect_regimes_threshold():
    # With a large threshold everything is neutral
    results = detect_regimes(RECORDS, commodity="CORN", threshold=100.0)
    assert all(r.regime == "neutral" for r in results)


def test_detect_regimes_empty_raises():
    with pytest.raises(RegimeError):
        detect_regimes([], commodity="CORN")


def test_detect_regimes_wrong_commodity_raises():
    with pytest.raises(RegimeError):
        detect_regimes(RECORDS, commodity="WHEAT")


def test_format_regimes_contains_header():
    results = detect_regimes(RECORDS, commodity="CORN")
    out = format_regimes(results)
    assert "Week" in out
    assert "Regime" in out


def test_format_regimes_shift_marker():
    results = detect_regimes(RECORDS, commodity="CORN")
    out = format_regimes(results)
    assert "<< SHIFT" in out
