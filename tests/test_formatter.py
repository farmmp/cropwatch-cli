"""Tests for cropwatch.formatter module."""

import pytest
from cropwatch.formatter import format_crop_progress, format_simple_table, _bar


SAMPLE_DATA = [
    {
        "year": "2023",
        "commodity_desc": "CORN",
        "week_ending": "2023-07-09",
        "short_desc": "CORN - CONDITION, EXCELLENT",
        "Value": "12",
    },
    {
        "year": "2023",
        "commodity_desc": "CORN",
        "week_ending": "2023-07-09",
        "short_desc": "CORN - CONDITION, GOOD",
        "Value": "55",
    },
    {
        "year": "2023",
        "commodity_desc": "CORN",
        "week_ending": "2023-07-09",
        "short_desc": "CORN - CONDITION, FAIR",
        "Value": "25",
    },
    {
        "year": "2023",
        "commodity_desc": "CORN",
        "week_ending": "2023-07-09",
        "short_desc": "CORN - CONDITION, POOR",
        "Value": "6",
    },
    {
        "year": "2023",
        "commodity_desc": "CORN",
        "week_ending": "2023-07-09",
        "short_desc": "CORN - CONDITION, VERY POOR",
        "Value": "2",
    },
]


def test_bar_empty():
    assert _bar(0) == "░" * 30


def test_bar_full():
    assert _bar(100) == "█" * 30


def test_bar_half():
    result = _bar(50)
    assert result.count("█") == 15
    assert result.count("░") == 15


def test_format_crop_progress_contains_header():
    output = format_crop_progress(SAMPLE_DATA, "corn", 2023)
    assert "Crop Progress: Corn (2023)" in output


def test_format_crop_progress_contains_week():
    output = format_crop_progress(SAMPLE_DATA, "corn", 2023)
    assert "2023-07-09" in output


def test_format_crop_progress_no_data():
    output = format_crop_progress(SAMPLE_DATA, "wheat", 2023)
    assert "No data found" in output


def test_format_crop_progress_case_insensitive():
    output_lower = format_crop_progress(SAMPLE_DATA, "corn", 2023)
    output_upper = format_crop_progress(SAMPLE_DATA, "CORN", 2023)
    assert output_lower == output_upper


def test_format_simple_table_headers():
    data = [{"name": "Alice", "score": "95"}, {"name": "Bob", "score": "87"}]
    output = format_simple_table(data, ["name", "score"])
    assert "NAME" in output
    assert "SCORE" in output
    assert "Alice" in output


def test_format_simple_table_empty():
    assert format_simple_table([], ["name"]) == "No data available."
