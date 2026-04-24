"""Unit tests for cropwatch.plateau."""

from __future__ import annotations

import pytest

from cropwatch.plateau import (
    PlateauError,
    PlateauResult,
    _extract_sorted,
    detect_plateaus,
    format_plateaus,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "IA") -> dict:
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "week_ending": week,
        "Value": str(value),
    }


# ---------------------------------------------------------------------------
# _extract_sorted
# ---------------------------------------------------------------------------

def test_extract_sorted_basic():
    records = [_rec("2023-05-14", 40.0), _rec("2023-05-07", 35.0)]
    result = _extract_sorted(records, "CORN", "IA")
    assert result == [(20230507, 35.0), (20230514, 40.0)]


def test_extract_sorted_filters_commodity():
    records = [_rec("2023-05-07", 35.0), _rec("2023-05-07", 20.0, commodity="SOYBEANS")]
    result = _extract_sorted(records, "CORN", "IA")
    assert len(result) == 1


def test_extract_sorted_filters_state():
    records = [_rec("2023-05-07", 35.0, state="IA"), _rec("2023-05-07", 40.0, state="IL")]
    result = _extract_sorted(records, "CORN", "IL")
    assert len(result) == 1
    assert result[0][1] == 40.0


def test_extract_sorted_skips_bad_value():
    records = [_rec("2023-05-07", 35.0), {"commodity_desc": "CORN", "state_alpha": "IA",
                                           "week_ending": "2023-05-14", "Value": "(D)"}]
    result = _extract_sorted(records, "CORN", "IA")
    assert len(result) == 1


# ---------------------------------------------------------------------------
# detect_plateaus
# ---------------------------------------------------------------------------

def test_detect_plateau_found():
    records = [
        _rec("2023-04-09", 50.0),
        _rec("2023-04-16", 50.5),
        _rec("2023-04-23", 50.2),
        _rec("2023-04-30", 50.8),
        _rec("2023-05-07", 70.0),  # jump — ends plateau
    ]
    results = detect_plateaus(records, "CORN", "IA", tolerance=1.0, min_length=3)
    assert len(results) == 1
    p = results[0]
    assert p.length == 4
    assert p.start_week == 20230409
    assert p.end_week == 20230430


def test_detect_no_plateau_when_too_short():
    records = [
        _rec("2023-04-09", 50.0),
        _rec("2023-04-16", 50.5),
        _rec("2023-04-23", 70.0),
    ]
    results = detect_plateaus(records, "CORN", "IA", tolerance=1.0, min_length=3)
    assert results == []


def test_detect_trailing_plateau():
    """Plateau that runs to the end of the series is still captured."""
    records = [
        _rec("2023-04-09", 20.0),
        _rec("2023-04-16", 60.0),  # big jump — resets run
        _rec("2023-04-23", 60.2),
        _rec("2023-04-30", 59.9),
        _rec("2023-05-07", 60.1),
    ]
    results = detect_plateaus(records, "CORN", "IA", tolerance=1.0, min_length=3)
    assert len(results) == 1
    assert results[0].end_week == 20230507


def test_detect_empty_raises():
    with pytest.raises(PlateauError):
        detect_plateaus([], "CORN", "IA")


def test_detect_avg_value():
    records = [
        _rec("2023-04-09", 50.0),
        _rec("2023-04-16", 50.0),
        _rec("2023-04-23", 50.0),
    ]
    results = detect_plateaus(records, "CORN", "IA", tolerance=1.0, min_length=3)
    assert len(results) == 1
    assert results[0].avg_value == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# format_plateaus
# ---------------------------------------------------------------------------

def test_format_plateaus_empty():
    out = format_plateaus([], "CORN")
    assert "No plateaus" in out


def test_format_plateaus_contains_data():
    p = PlateauResult(
        commodity="CORN", state="IA",
        start_week=20230409, end_week=20230430,
        length=4, avg_value=50.2,
    )
    out = format_plateaus([p], "CORN")
    assert "20230409" in out
    assert "50.2" in out
    assert "CORN" in out
