"""Tests for cropwatch.dominance."""
from __future__ import annotations

import pytest

from cropwatch.dominance import (
    DominanceError,
    DominanceResult,
    _extract_keyed,
    compute_dominance,
    format_dominance,
)


def _rec(state: str, week: str, value: float, commodity: str = "CORN", attr: str = "PROGRESS") -> dict:
    return {
        "state_alpha": state,
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": commodity,
        "short_desc": f"{commodity} - {attr} PCT",
    }


records = [
    _rec("IA", "2023-05-01", 80.0),
    _rec("IL", "2023-05-01", 70.0),
    _rec("MN", "2023-05-01", 60.0),
    _rec("IA", "2023-05-08", 75.0),
    _rec("IL", "2023-05-08", 85.0),
    _rec("MN", "2023-05-08", 65.0),
    _rec("IA", "2023-05-15", 90.0),
    _rec("IL", "2023-05-15", 88.0),
    _rec("MN", "2023-05-15", 70.0),
]


def test_extract_keyed_basic():
    keyed = _extract_keyed(records, "CORN", "PROGRESS")
    assert "IA" in keyed
    assert "IL" in keyed
    assert "MN" in keyed


def test_extract_keyed_excludes_us():
    recs = records + [_rec("US", "2023-05-01", 99.0)]
    keyed = _extract_keyed(recs, "CORN", "PROGRESS")
    assert "US" not in keyed


def test_extract_keyed_filters_commodity():
    keyed = _extract_keyed(records, "SOYBEANS", "PROGRESS")
    assert keyed == {}


def test_extract_keyed_skips_bad_value():
    bad = records + [{
        "state_alpha": "KS",
        "week_ending": "2023-05-01",
        "Value": "N/A",
        "commodity_desc": "CORN",
        "short_desc": "CORN - PROGRESS PCT",
    }]
    keyed = _extract_keyed(bad, "CORN", "PROGRESS")
    assert "KS" not in keyed


def test_compute_basic_length():
    results = compute_dominance(records, "CORN", "PROGRESS", top_n=3)
    assert len(results) <= 3


def test_compute_leader_is_ia():
    # IA leads weeks 1 and 3, IL leads week 2 → IA should rank first
    results = compute_dominance(records, "CORN", "PROGRESS")
    assert results[0].state == "IA"
    assert results[0].weeks_leading == 2


def test_compute_avg_value():
    results = compute_dominance(records, "CORN", "PROGRESS")
    ia = next(r for r in results if r.state == "IA")
    assert ia.avg_value == pytest.approx((80 + 75 + 90) / 3, rel=1e-3)


def test_compute_max_value():
    results = compute_dominance(records, "CORN", "PROGRESS")
    ia = next(r for r in results if r.state == "IA")
    assert ia.max_value == 90.0


def test_compute_empty_raises():
    with pytest.raises(DominanceError, match="No records"):
        compute_dominance([], "CORN", "PROGRESS")


def test_compute_no_matching_raises():
    with pytest.raises(DominanceError):
        compute_dominance(records, "WHEAT", "PROGRESS")


def test_format_dominance_contains_state():
    results = compute_dominance(records, "CORN", "PROGRESS")
    output = format_dominance(results)
    assert "IA" in output


def test_format_dominance_empty():
    assert format_dominance([]) == "No dominance data."
