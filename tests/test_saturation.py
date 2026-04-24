"""Tests for cropwatch.saturation."""
import pytest

from cropwatch.saturation import (
    SaturationError,
    SaturationResult,
    detect_saturation,
    format_saturation,
)


def _rec(week: str, value, commodity: str = "CORN", state: str = "US") -> dict:
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "week_ending": week,
        "Value": value,
    }


RECORDS = [
    _rec("2023-04-10", 2.0),   # floor
    _rec("2023-04-17", 45.0),  # normal
    _rec("2023-04-24", 97.0),  # ceiling
    _rec("2023-05-01", 5.0),   # exactly at default low -> floor
    _rec("2023-05-08", 95.0),  # exactly at default high -> ceiling
]


def test_detect_finds_floor():
    results = detect_saturation(RECORDS, commodity="CORN", attribute="Value")
    floors = [r for r in results if r.kind == "floor"]
    assert len(floors) == 2
    assert floors[0].week_ending == "2023-04-10"


def test_detect_finds_ceiling():
    results = detect_saturation(RECORDS, commodity="CORN", attribute="Value")
    ceilings = [r for r in results if r.kind == "ceiling"]
    assert len(ceilings) == 2
    assert ceilings[0].week_ending == "2023-04-24"


def test_detect_skips_normal():
    results = detect_saturation(RECORDS, commodity="CORN", attribute="Value")
    weeks = {r.week_ending for r in results}
    assert "2023-04-17" not in weeks


def test_detect_empty_raises():
    with pytest.raises(SaturationError, match="No records found"):
        detect_saturation([], commodity="CORN", attribute="Value")


def test_detect_wrong_commodity_raises():
    with pytest.raises(SaturationError):
        detect_saturation(RECORDS, commodity="WHEAT", attribute="Value")


def test_detect_filters_state():
    records = [
        _rec("2023-04-10", 2.0, state="IA"),
        _rec("2023-04-17", 98.0, state="IL"),
    ]
    results = detect_saturation(records, commodity="CORN", attribute="Value", state="IA")
    assert len(results) == 1
    assert results[0].state if hasattr(results[0], "state") else results[0].week_ending == "2023-04-10"


def test_detect_skips_non_numeric():
    records = [
        _rec("2023-04-10", "N/A"),
        _rec("2023-04-17", 2.0),
    ]
    results = detect_saturation(records, commodity="CORN", attribute="Value")
    assert len(results) == 1


def test_custom_thresholds():
    records = [_rec("2023-04-10", 10.0)]
    results = detect_saturation(records, commodity="CORN", attribute="Value", low=15.0, high=90.0)
    assert len(results) == 1
    assert results[0].kind == "floor"


def test_format_saturation_no_results():
    output = format_saturation([], "CORN")
    assert "No saturation" in output


def test_format_saturation_contains_header():
    results = [SaturationResult("2023-04-10", 2.0, "floor")]
    output = format_saturation(results, "CORN")
    assert "CORN" in output
    assert "Week" in output
    assert "floor" in output


def test_format_saturation_row_count():
    results = [
        SaturationResult("2023-04-10", 2.0, "floor"),
        SaturationResult("2023-04-24", 97.0, "ceiling"),
    ]
    lines = format_saturation(results, "CORN").splitlines()
    # header (1) + column row (1) + separator (1) + 2 data rows = 5
    assert len(lines) == 5
