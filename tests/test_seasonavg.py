"""Tests for cropwatch.seasonavg."""
import pytest
from cropwatch.seasonavg import (
    compute_season_avg,
    format_season_avg,
    SeasonAvgError,
    SeasonAvgResult,
)


def _rec(commodity, state, value):
    return {"commodity_desc": commodity, "state_alpha": state, "Value": value}


RECORDS = [
    _rec("CORN", "US", "80"),
    _rec("CORN", "US", "60"),
    _rec("CORN", "US", "70"),
    _rec("SOYBEANS", "US", "50"),
    _rec("CORN", "IA", "90"),
]


def test_compute_basic():
    result = compute_season_avg(RECORDS, "CORN")
    assert result.week_count == 3
    assert result.average == pytest.approx(70.0)
    assert result.minimum == 60.0
    assert result.maximum == 80.0


def test_compute_filters_state():
    result = compute_season_avg(RECORDS, "CORN", state="IA")
    assert result.week_count == 1
    assert result.average == 90.0


def test_compute_empty_raises():
    with pytest.raises(SeasonAvgError, match="No records"):
        compute_season_avg([], "CORN")


def test_compute_no_matching_raises():
    with pytest.raises(SeasonAvgError, match="No numeric values"):
        compute_season_avg(RECORDS, "WHEAT")


def test_compute_skips_non_numeric():
    recs = RECORDS + [_rec("CORN", "US", "(D)")]
    result = compute_season_avg(recs, "CORN")
    assert result.week_count == 3


def test_compute_case_insensitive():
    result = compute_season_avg(RECORDS, "corn")
    assert result.commodity == "corn"
    assert result.week_count == 3


def test_format_contains_commodity():
    result = SeasonAvgResult("CORN", "US", 3, 70.0, 60.0, 80.0)
    out = format_season_avg(result)
    assert "CORN" in out
    assert "70.0" in out
    assert "60.0" in out
    assert "80.0" in out
    assert "3" in out
