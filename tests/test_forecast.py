"""Tests for cropwatch.forecast."""
import pytest
from cropwatch.forecast import (
    ForecastError,
    ForecastResult,
    _linear_fit,
    forecast,
    extract_series,
    format_forecast,
)


def test_linear_fit_basic():
    slope, intercept = _linear_fit([0.0, 1.0, 2.0, 3.0])
    assert abs(slope - 1.0) < 1e-6
    assert abs(intercept) < 1e-6


def test_linear_fit_too_few_points():
    with pytest.raises(ForecastError, match="at least 2"):
        _linear_fit([5.0])


def test_forecast_returns_result():
    values = [10.0, 20.0, 30.0, 40.0]
    result = forecast(values, weeks_ahead=1)
    assert isinstance(result, ForecastResult)
    assert result.predicted_value == 50.0
    assert result.weeks_ahead == 1


def test_forecast_clamps_to_100():
    values = [90.0, 95.0, 98.0, 99.0]
    result = forecast(values, weeks_ahead=10)
    assert result.predicted_value <= 100.0


def test_forecast_clamps_to_zero():
    values = [5.0, 3.0, 1.0]
    result = forecast(values, weeks_ahead=10)
    assert result.predicted_value >= 0.0


def test_forecast_invalid_weeks_ahead():
    with pytest.raises(ForecastError, match="weeks_ahead"):
        forecast([10.0, 20.0], weeks_ahead=0)


def test_extract_series_basic():
    records = [
        {"commodity_desc": "Corn", "Value": "30"},
        {"commodity_desc": "Corn", "Value": "45"},
        {"commodity_desc": "Soybeans", "Value": "20"},
    ]
    series = extract_series(records, "corn")
    assert series == [30.0, 45.0]


def test_extract_series_filters_na():
    records = [
        {"commodity_desc": "Corn", "Value": "(NA)"},
        {"commodity_desc": "Corn", "Value": "50"},
    ]
    assert extract_series(records, "corn") == [50.0]


def test_extract_series_bad_value():
    records = [{"commodity_desc": "Corn", "Value": "N/A"}]
    with pytest.raises(ForecastError):
        extract_series(records, "corn")


def test_format_forecast_contains_commodity():
    result = ForecastResult(weeks_ahead=2, predicted_value=67.5, slope=2.1, intercept=5.0)
    output = format_forecast(result, "corn")
    assert "Corn" in output
    assert "67.5%" in output
    assert "+2" in output
