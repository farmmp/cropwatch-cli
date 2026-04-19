"""Tests for cropwatch.smooth."""
import pytest
from cropwatch.smooth import _rolling_avg, smooth_series, format_smooth, SmoothError, SmoothedSeries


def _rec(week, value, commodity="CORN"):
    return {"week_ending": week, "Value": str(value), "commodity_desc": commodity}


RECORDS = [
    _rec("2023-04-01", 10),
    _rec("2023-04-08", 20),
    _rec("2023-04-15", 30),
    _rec("2023-04-22", 40),
]


def test_rolling_avg_window1():
    assert _rolling_avg([10.0, 20.0, 30.0], 1) == [10.0, 20.0, 30.0]


def test_rolling_avg_window3():
    result = _rolling_avg([10.0, 20.0, 30.0], 3)
    assert result[0] == pytest.approx(10.0)
    assert result[1] == pytest.approx(15.0)
    assert result[2] == pytest.approx(20.0)


def test_smooth_series_basic():
    s = smooth_series(RECORDS, commodity="CORN", window=2)
    assert isinstance(s, SmoothedSeries)
    assert len(s.weeks) == 4
    assert len(s.smoothed) == 4
    assert s.window == 2


def test_smooth_series_values():
    s = smooth_series(RECORDS, commodity="CORN", window=1)
    assert s.smoothed == pytest.approx([10.0, 20.0, 30.0, 40.0])


def test_smooth_series_empty_raises():
    with pytest.raises(SmoothError, match="No records"):
        smooth_series([], commodity="CORN")


def test_smooth_series_bad_window_raises():
    with pytest.raises(SmoothError, match="Window"):
        smooth_series(RECORDS, commodity="CORN", window=0)


def test_smooth_series_unknown_commodity_raises():
    with pytest.raises(SmoothError, match="No records found"):
        smooth_series(RECORDS, commodity="WHEAT")


def test_smooth_series_skips_non_numeric():
    recs = RECORDS + [{"week_ending": "2023-04-29", "Value": "N/A", "commodity_desc": "CORN"}]
    s = smooth_series(recs, commodity="CORN", window=2)
    assert len(s.original) == 4


def test_format_smooth_contains_header():
    s = smooth_series(RECORDS, commodity="CORN", window=3)
    out = format_smooth(s, "CORN")
    assert "Smoothed Series" in out
    assert "CORN" in out.upper()
    assert "Actual" in out


def test_format_smooth_row_count():
    s = smooth_series(RECORDS, commodity="CORN", window=2)
    out = format_smooth(s, "CORN")
    data_lines = [l for l in out.splitlines() if "2023" in l]
    assert len(data_lines) == 4
