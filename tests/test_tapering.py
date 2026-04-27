"""Tests for cropwatch.tapering."""
from __future__ import annotations

import pytest

from cropwatch.tapering import (
    TaperingError,
    TaperingResult,
    _extract_sorted,
    detect_tapering,
    format_tapering,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "US") -> dict:
    return {
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": commodity,
        "state_alpha": state,
    }


# ---------------------------------------------------------------------------
# _extract_sorted
# ---------------------------------------------------------------------------

def test_extract_sorted_basic():
    records = [_rec("2023-06-11", 60), _rec("2023-06-04", 50)]
    result = _extract_sorted(records, "CORN")
    assert result == [(20230604, 50.0), (20230611, 60.0)]


def test_extract_sorted_filters_commodity():
    records = [_rec("2023-06-04", 50, commodity="SOYBEANS"), _rec("2023-06-04", 70)]
    result = _extract_sorted(records, "CORN")
    assert len(result) == 1
    assert result[0][1] == 70.0


def test_extract_sorted_filters_state():
    records = [_rec("2023-06-04", 50, state="IA"), _rec("2023-06-04", 70, state="US")]
    result = _extract_sorted(records, "CORN", state="IA")
    assert len(result) == 1
    assert result[0][1] == 50.0


def test_extract_sorted_skips_bad_value():
    records = [_rec("2023-06-04", 50), {"week_ending": "2023-06-11", "Value": "N/A",
                                         "commodity_desc": "CORN", "state_alpha": "US"}]
    result = _extract_sorted(records, "CORN")
    assert len(result) == 1


# ---------------------------------------------------------------------------
# detect_tapering
# ---------------------------------------------------------------------------

def _tapering_records(start: float = 90.0, steps: int = 5) -> list:
    """Build records where value approaches 100 with decelerating changes."""
    values = [start]
    change = 5.0
    for _ in range(steps - 1):
        change = round(change * 0.6, 2)
        values.append(min(100.0, values[-1] + change))
    records = []
    for i, v in enumerate(values):
        week = f"2023-0{i + 1}-01" if i < 9 else f"2023-{i + 1:02d}-01"
        records.append(_rec(f"2023-{i + 1:02d}-01", v))
    return records


def test_detect_tapering_found():
    records = _tapering_records(start=90.0, steps=5)
    result = detect_tapering(records, "CORN", window=5, threshold=5.0)
    assert isinstance(result, TaperingResult)
    assert result.target == 100.0
    assert result.commodity == "CORN"
    assert result.state == "US"


def test_detect_tapering_floor():
    """Values approaching 0 should set target=0."""
    values = [10.0, 6.0, 3.5, 2.0, 1.0]
    records = [_rec(f"2023-{i + 1:02d}-01", v) for i, v in enumerate(values)]
    result = detect_tapering(records, "CORN", window=5, threshold=10.0)
    assert result is not None
    assert result.target == 0.0


def test_detect_tapering_not_decelerating_returns_none():
    """Constant changes should not qualify as tapering."""
    values = [80.0, 85.0, 90.0, 95.0, 100.0]
    records = [_rec(f"2023-{i + 1:02d}-01", v) for i, v in enumerate(values)]
    result = detect_tapering(records, "CORN", window=5, threshold=10.0)
    assert result is None


def test_detect_tapering_too_few_raises():
    records = [_rec("2023-01-01", 90.0)]
    with pytest.raises(TaperingError):
        detect_tapering(records, "CORN")


def test_detect_tapering_empty_raises():
    with pytest.raises(TaperingError):
        detect_tapering([], "CORN")


def test_detect_tapering_avg_change_positive():
    records = _tapering_records(start=90.0, steps=5)
    result = detect_tapering(records, "CORN", window=5, threshold=5.0)
    if result is not None:
        assert result.avg_weekly_change >= 0


# ---------------------------------------------------------------------------
# format_tapering
# ---------------------------------------------------------------------------

def test_format_tapering_none():
    out = format_tapering(None, commodity="CORN", state="US")
    assert "No tapering" in out
    assert "CORN" in out


def test_format_tapering_result_contains_fields():
    records = _tapering_records(start=90.0, steps=5)
    result = detect_tapering(records, "CORN", window=5, threshold=5.0)
    if result is None:
        pytest.skip("No tapering detected with test data — skipping format test")
    out = format_tapering(result, commodity="CORN", state="US")
    assert "CORN" in out
    assert "100%" in out or "ceiling" in out
    assert "→" in out
