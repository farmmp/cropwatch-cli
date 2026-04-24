"""Tests for cropwatch.seasonality."""
from __future__ import annotations

import pytest

from cropwatch.seasonality import (
    SeasonalityError,
    SeasonalityResult,
    _extract_week_averages,
    compute_seasonality,
    format_seasonality,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "IA") -> dict:
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "week_ending": week,
        "Value": str(value),
    }


records = [
    _rec("2023-04-01", 10.0),
    _rec("2023-04-08", 45.0),
    _rec("2023-04-15", 80.0),  # peak
    _rec("2023-04-22", 30.0),
    _rec("2023-04-29", 5.0),   # trough
]


def test_compute_basic_peak_and_trough():
    result = compute_seasonality(records, commodity="CORN", state="IA")
    assert result.peak_week == "2023-04-15"
    assert result.trough_week == "2023-04-29"


def test_compute_peak_avg_value():
    result = compute_seasonality(records, commodity="CORN", state="IA")
    assert result.peak_avg == pytest.approx(80.0)
    assert result.trough_avg == pytest.approx(5.0)


def test_compute_week_averages_count():
    result = compute_seasonality(records, commodity="CORN", state="IA")
    assert len(result.week_averages) == 5


def test_compute_empty_raises():
    with pytest.raises(SeasonalityError, match="No records"):
        compute_seasonality([], commodity="CORN")


def test_compute_no_matching_raises():
    with pytest.raises(SeasonalityError, match="No numeric data"):
        compute_seasonality(records, commodity="WHEAT", state="IA")


def test_compute_filters_state():
    extra = records + [_rec("2023-04-15", 99.0, state="IL")]
    result = compute_seasonality(extra, commodity="CORN", state="IA")
    # IL record should not affect IA peak
    assert result.peak_avg == pytest.approx(80.0)


def test_compute_no_state_aggregates_all():
    mixed = [
        _rec("2023-04-01", 20.0, state="IA"),
        _rec("2023-04-01", 40.0, state="IL"),
    ]
    result = compute_seasonality(mixed, commodity="CORN", state=None)
    assert result.week_averages["2023-04-01"] == pytest.approx(30.0)


def test_extract_week_averages_skips_bad_values():
    bad = records + [{"commodity_desc": "CORN", "state_alpha": "IA", "week_ending": "2023-05-01", "Value": "(D)"}]
    avgs = _extract_week_averages(bad, "CORN", "IA")
    assert "2023-05-01" not in avgs


def test_format_seasonality_contains_commodity():
    result = compute_seasonality(records, commodity="CORN", state="IA")
    output = format_seasonality(result)
    assert "CORN" in output
    assert "IA" in output


def test_format_seasonality_shows_peak_week():
    result = compute_seasonality(records, commodity="CORN", state="IA")
    output = format_seasonality(result)
    assert "2023-04-15" in output
    assert "2023-04-29" in output


def test_format_seasonality_us_label_when_no_state():
    mixed = [
        _rec("2023-04-01", 20.0, state="IA"),
        _rec("2023-04-08", 50.0, state="IA"),
    ]
    result = compute_seasonality(mixed, commodity="CORN", state=None)
    output = format_seasonality(result)
    assert "US" in output
