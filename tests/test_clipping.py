"""Tests for cropwatch.clipping."""
from __future__ import annotations

import pytest

from cropwatch.clipping import (
    ClippingError,
    ClippingResult,
    detect_clipping,
    format_clipping,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "IL") -> dict:
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "week_ending": week,
        "Value": str(value),
    }


# ---------------------------------------------------------------------------
# _extract_sorted (indirectly via detect_clipping)
# ---------------------------------------------------------------------------

def test_extract_sorted_filters_commodity():
    records = [_rec("2023-01-01", 0.0), _rec("2023-01-01", 0.0, commodity="SOYBEANS")]
    results = detect_clipping(records, commodity="CORN", state="IL", min_consecutive=1)
    assert all(r.commodity == "CORN" for r in results)


def test_extract_sorted_filters_state():
    records = [_rec("2023-01-01", 0.0, state="IL"), _rec("2023-01-01", 0.0, state="IA")]
    results = detect_clipping(records, commodity="CORN", state="IL", min_consecutive=1)
    assert all(r.state == "IL" for r in results)


def test_extract_sorted_skips_bad_value():
    records = [_rec("2023-01-01", 0.0), {"commodity_desc": "CORN", "state_alpha": "IL", "week_ending": "2023-01-08", "Value": "N/A"}]
    results = detect_clipping(records, commodity="CORN", state="IL", min_consecutive=1)
    assert len(results) == 1


# ---------------------------------------------------------------------------
# detect_clipping
# ---------------------------------------------------------------------------

def test_detect_clipping_floor():
    records = [
        _rec("2023-01-01", 0.0),
        _rec("2023-01-08", 0.0),
        _rec("2023-01-15", 5.0),
    ]
    results = detect_clipping(records, commodity="CORN", state="IL", min_consecutive=2)
    assert len(results) == 2
    assert all(r.boundary == "floor" for r in results)


def test_detect_clipping_ceiling():
    records = [
        _rec("2023-01-01", 50.0),
        _rec("2023-01-08", 100.0),
        _rec("2023-01-15", 100.0),
        _rec("2023-01-22", 100.0),
    ]
    results = detect_clipping(records, commodity="CORN", state="IL", min_consecutive=2)
    assert len(results) == 3
    assert all(r.boundary == "ceiling" for r in results)


def test_detect_clipping_below_min_run_not_flagged():
    records = [
        _rec("2023-01-01", 0.0),
        _rec("2023-01-08", 5.0),
    ]
    results = detect_clipping(records, commodity="CORN", state="IL", min_consecutive=2)
    assert results == []


def test_detect_clipping_no_data_raises():
    with pytest.raises(ClippingError):
        detect_clipping([], commodity="CORN", min_consecutive=1)


def test_detect_clipping_no_state_filter():
    records = [
        _rec("2023-01-01", 0.0, state="IL"),
        _rec("2023-01-08", 0.0, state="IA"),
    ]
    # Without state filter both records are included; run length is 1 each (different sort keys)
    results = detect_clipping(records, commodity="CORN", state=None, min_consecutive=1)
    assert len(results) == 2


# ---------------------------------------------------------------------------
# format_clipping
# ---------------------------------------------------------------------------

def test_format_clipping_no_results():
    out = format_clipping([], "CORN")
    assert "No clipping" in out


def test_format_clipping_contains_commodity():
    results = [ClippingResult(commodity="CORN", state="IL", week_ending="2023-01-01", value=0.0, boundary="floor")]
    out = format_clipping(results, "CORN")
    assert "CORN" in out
    assert "floor" in out
    assert "2023-01-01" in out
