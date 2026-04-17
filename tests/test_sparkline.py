"""Tests for cropwatch.sparkline."""
import pytest
from cropwatch.sparkline import (
    normalize,
    sparkline,
    format_trend_table,
    SparklineError,
)


def test_normalize_empty():
    assert normalize([]) == []


def test_normalize_uniform():
    result = normalize([5.0, 5.0, 5.0])
    assert all(v == 0.5 for v in result)


def test_normalize_range():
    result = normalize([0.0, 50.0, 100.0])
    assert result[0] == pytest.approx(0.0)
    assert result[1] == pytest.approx(0.5)
    assert result[2] == pytest.approx(1.0)


def test_sparkline_empty_raises():
    with pytest.raises(SparklineError):
        sparkline([])


def test_sparkline_length_matches():
    values = [10.0, 20.0, 30.0, 40.0]
    result = sparkline(values)
    assert len(result) == len(values)


def test_sparkline_ascending():
    values = [0.0, 25.0, 50.0, 75.0, 100.0]
    result = sparkline(values)
    # Each char should be >= previous (non-decreasing)
    for a, b in zip(result, result[1:]):
        assert a <= b


def test_sparkline_uniform():
    values = [42.0, 42.0, 42.0]
    result = sparkline(values)
    assert len(set(result)) == 1


def test_format_trend_table_no_data():
    assert "No trend data" in format_trend_table([])


def test_format_trend_table_contains_trend():
    records = [
        {"Week_Ending": "2024-04-07", "Value": "30"},
        {"Week_Ending": "2024-04-14", "Value": "55"},
        {"Week_Ending": "2024-04-21", "Value": "80"},
    ]
    output = format_trend_table(records)
    assert "Trend:" in output
    assert "2024-04-07" in output


def test_format_trend_table_handles_missing_value():
    records = [
        {"Week_Ending": "2024-04-07"},
        {"Week_Ending": "2024-04-14", "Value": "60"},
    ]
    output = format_trend_table(records)
    assert "Trend:" in output
