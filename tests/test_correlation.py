"""Tests for cropwatch.correlation."""
import pytest
from cropwatch.correlation import (
    correlate, format_correlation, _extract_series,
    CorrelationResult, CorrelationError,
)


def _rec(commodity, week, value):
    return {"commodity_desc": commodity, "week_ending": week, "Value": str(value)}


CORN = "CORN"
SOY = "SOYBEANS"


@pytest.fixture()
def shared_records():
    weeks = [f"2023-0{i}-01" for i in range(1, 8)]
    corn_vals = [10, 20, 30, 40, 50, 60, 70]
    soy_vals  = [12, 22, 31, 41, 52, 61, 69]
    records = []
    for w, cv, sv in zip(weeks, corn_vals, soy_vals):
        records.append(_rec(CORN, w, cv))
        records.append(_rec(SOY, w, sv))
    return records


def test_extract_series_basic(shared_records):
    s = _extract_series(shared_records, CORN)
    assert len(s) == 7
    assert s["2023-01-01"] == 10.0


def test_extract_series_ignores_bad_values():
    recs = [_rec(CORN, "2023-01-01", "N/A"), _rec(CORN, "2023-02-01", 25)]
    s = _extract_series(recs, CORN)
    assert "2023-01-01" not in s
    assert s["2023-02-01"] == 25.0


def test_correlate_high_positive(shared_records):
    result = correlate(shared_records, CORN, SOY)
    assert isinstance(result, CorrelationResult)
    assert result.r > 0.99
    assert result.n == 7


def test_correlate_negative():
    weeks = [f"2023-0{i}-01" for i in range(1, 6)]
    records = []
    for i, w in enumerate(weeks):
        records.append(_rec(CORN, w, (i + 1) * 10))
        records.append(_rec(SOY, w, (5 - i) * 10))
    result = correlate(records, CORN, SOY)
    assert result.r < -0.99


def test_correlate_empty_raises():
    with pytest.raises(CorrelationError, match="No records"):
        correlate([], CORN, SOY)


def test_correlate_too_few_shared_raises():
    records = [_rec(CORN, "2023-01-01", 10), _rec(SOY, "2023-02-01", 20)]
    with pytest.raises(CorrelationError, match="Not enough shared"):
        correlate(records, CORN, SOY)


def test_correlate_zero_variance_raises():
    weeks = [f"2023-0{i}-01" for i in range(1, 5)]
    records = []
    for w in weeks:
        records.append(_rec(CORN, w, 50))
        records.append(_rec(SOY, w, 50))
    with pytest.raises(CorrelationError, match="Zero variance"):
        correlate(records, CORN, SOY)


def test_format_correlation_contains_r(shared_records):
    result = correlate(shared_records, CORN, SOY)
    out = format_correlation(result)
    assert "Pearson r" in out
    assert CORN in out
    assert SOY in out


def test_format_correlation_strength_label():
    result = CorrelationResult(commodity_a=CORN, commodity_b=SOY, r=0.85, n=10)
    out = format_correlation(result)
    assert "strong" in out
    assert "positive" in out
