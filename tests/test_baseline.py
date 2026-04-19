"""Tests for cropwatch.baseline."""
import pytest
from cropwatch.baseline import compute_baseline, format_baseline, BaselineError, BaselineResult


def _rec(year, week, commodity, value):
    return {"year": year, "week_ending": week, "commodity_desc": commodity, "Value": value}


WEEK = "2024-06-02"
CROP = "Corn"


@pytest.fixture
def records():
    return [
        _rec(2021, WEEK, CROP, "72"),
        _rec(2022, WEEK, CROP, "68"),
        _rec(2023, WEEK, CROP, "74"),
        _rec(2024, WEEK, CROP, "80"),
    ]


def test_compute_basic(records):
    result = compute_baseline(records, CROP, WEEK, current_year=2024)
    assert isinstance(result, BaselineResult)
    assert result.current == 80.0
    assert result.average == pytest.approx((72 + 68 + 74) / 3, rel=1e-3)
    assert result.delta == pytest.approx(80.0 - (72 + 68 + 74) / 3, rel=1e-3)


def test_compute_empty_raises():
    with pytest.raises(BaselineError, match="No records"):
        compute_baseline([], CROP, WEEK, current_year=2024)


def test_compute_no_matching_week(records):
    with pytest.raises(BaselineError, match="No records found"):
        compute_baseline(records, CROP, "1999-01-01", current_year=2024)


def test_compute_no_current_year(records):
    with pytest.raises(BaselineError, match="No data for current year"):
        compute_baseline(records, CROP, WEEK, current_year=2099)


def test_compute_no_historical():
    recs = [_rec(2024, WEEK, CROP, "80")]
    with pytest.raises(BaselineError, match="No historical"):
        compute_baseline(recs, CROP, WEEK, current_year=2024)


def test_std_dev_single_historical():
    recs = [
        _rec(2023, WEEK, CROP, "70"),
        _rec(2024, WEEK, CROP, "80"),
    ]
    result = compute_baseline(recs, CROP, WEEK, current_year=2024)
    assert result.std_dev == 0.0


def test_format_baseline_contains_delta(records):
    result = compute_baseline(records, CROP, WEEK, current_year=2024)
    output = format_baseline(result)
    assert "Delta" in output
    assert "Baseline Report" in output
    assert CROP in output
