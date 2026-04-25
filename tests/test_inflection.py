"""Unit tests for cropwatch.inflection."""

from __future__ import annotations

import pytest

from cropwatch.inflection import (
    InflectionError,
    InflectionPoint,
    _extract_sorted,
    detect_inflections,
    format_inflections,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "US") -> dict:
    return {
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": commodity,
        "state_alpha": state,
    }


# --- _extract_sorted ---

def test_extract_sorted_basic():
    records = [_rec("2023-05-14", 30.0), _rec("2023-05-07", 20.0), _rec("2023-05-21", 25.0)]
    result = _extract_sorted(records, "CORN", None)
    assert [r[0] for r in result] == ["2023-05-07", "2023-05-14", "2023-05-21"]


def test_extract_sorted_filters_commodity():
    records = [_rec("2023-05-07", 20.0, "CORN"), _rec("2023-05-07", 15.0, "SOYBEANS")]
    result = _extract_sorted(records, "SOYBEANS", None)
    assert len(result) == 1
    assert result[0][1] == 15.0


def test_extract_sorted_filters_state():
    records = [_rec("2023-05-07", 20.0, state="IA"), _rec("2023-05-07", 30.0, state="IL")]
    result = _extract_sorted(records, "CORN", "IA")
    assert len(result) == 1
    assert result[0][1] == 20.0


def test_extract_sorted_skips_bad_value():
    records = [_rec("2023-05-07", 20.0), {"week_ending": "2023-05-14", "Value": "N/A", "commodity_desc": "CORN", "state_alpha": "US"}]
    result = _extract_sorted(records, "CORN", None)
    assert len(result) == 1


# --- detect_inflections ---

def test_detect_inflections_too_few_raises():
    records = [_rec("2023-05-07", 10.0), _rec("2023-05-14", 20.0)]
    with pytest.raises(InflectionError):
        detect_inflections(records, "CORN")


def test_detect_finds_peak():
    # goes up then down — peak at week 2
    records = [
        _rec("2023-05-07", 10.0),
        _rec("2023-05-14", 50.0),
        _rec("2023-05-21", 20.0),
    ]
    result = detect_inflections(records, "CORN", min_change=2.0)
    assert len(result) == 1
    assert result[0].prior_direction == "up"
    assert result[0].new_direction == "down"


def test_detect_finds_trough():
    # goes down then up — trough at week 2
    records = [
        _rec("2023-05-07", 50.0),
        _rec("2023-05-14", 10.0),
        _rec("2023-05-21", 40.0),
    ]
    result = detect_inflections(records, "CORN", min_change=2.0)
    assert len(result) == 1
    assert result[0].prior_direction == "down"
    assert result[0].new_direction == "up"


def test_detect_no_inflection_monotone():
    records = [
        _rec("2023-05-07", 10.0),
        _rec("2023-05-14", 20.0),
        _rec("2023-05-21", 30.0),
    ]
    result = detect_inflections(records, "CORN", min_change=2.0)
    assert result == []


def test_detect_respects_min_change():
    # tiny fluctuation should not count
    records = [
        _rec("2023-05-07", 10.0),
        _rec("2023-05-14", 11.0),
        _rec("2023-05-21", 10.5),
    ]
    result = detect_inflections(records, "CORN", min_change=2.0)
    assert result == []


# --- format_inflections ---

def test_format_inflections_empty():
    out = format_inflections([], "CORN")
    assert "No inflection" in out


def test_format_inflections_contains_week():
    pts = [InflectionPoint(week_ending="2023-05-14", value=50.0, prior_direction="up", new_direction="down")]
    out = format_inflections(pts, "CORN")
    assert "2023-05-14" in out
    assert "up" in out
    assert "down" in out
