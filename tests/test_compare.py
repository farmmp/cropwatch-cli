import pytest
from cropwatch.compare import compare_years, format_comparison, extract_week_value, CompareError

RECORDS_2024 = [
    {"week_ending": "2024-05-05", "commodity_desc": "CORN", "Value": "62"},
    {"week_ending": "2024-05-05", "commodity_desc": "SOYBEANS", "Value": "45"},
]

RECORDS_2023 = [
    {"week_ending": "2024-05-05", "commodity_desc": "CORN", "Value": "55"},
    {"week_ending": "2024-05-05", "commodity_desc": "SOYBEANS", "Value": "50"},
]


def test_extract_week_value_found():
    val = extract_week_value(RECORDS_2024, "2024-05-05", "CORN")
    assert val == 62.0


def test_extract_week_value_missing():
    val = extract_week_value(RECORDS_2024, "2024-05-05", "WHEAT")
    assert val is None


def test_compare_years_basic():
    result = compare_years(RECORDS_2024, RECORDS_2023, "CORN", "2024-05-05")
    assert result["current"] == 62.0
    assert result["previous"] == 55.0
    assert result["delta"] == 7.0
    assert result["pct_change"] == pytest.approx(12.73, rel=1e-2)


def test_compare_years_negative_delta():
    result = compare_years(RECORDS_2024, RECORDS_2023, "SOYBEANS", "2024-05-05")
    assert result["delta"] == -5.0
    assert result["pct_change"] == pytest.approx(-10.0)


def test_compare_years_missing_both_raises():
    with pytest.raises(CompareError):
        compare_years(RECORDS_2024, RECORDS_2023, "WHEAT", "2024-05-05")


def test_compare_years_missing_previous():
    result = compare_years(RECORDS_2024, [], "CORN", "2024-05-05")
    assert result["previous"] is None
    assert result["delta"] is None


def test_format_comparison_contains_commodity():
    result = compare_years(RECORDS_2024, RECORDS_2023, "CORN", "2024-05-05")
    output = format_comparison(result)
    assert "CORN" in output
    assert "62" in output
    assert "55" in output


def test_format_comparison_arrow_up():
    result = compare_years(RECORDS_2024, RECORDS_2023, "CORN", "2024-05-05")
    output = format_comparison(result)
    assert "▲" in output


def test_format_comparison_arrow_down():
    result = compare_years(RECORDS_2024, RECORDS_2023, "SOYBEANS", "2024-05-05")
    output = format_comparison(result)
    assert "▼" in output
