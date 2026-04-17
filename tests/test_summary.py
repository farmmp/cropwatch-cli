"""Tests for cropwatch.summary."""
import pytest
from cropwatch.summary import compute_summary, format_summary, SummaryError


SAMPLE_RECORDS = [
    {"Week": "2024-04-07", "Value": "55"},
    {"Week": "2024-04-14", "Value": "60"},
    {"Week": "2024-04-21", "Value": "70"},
    {"Week": "2024-04-28", "Value": "80"},
]


def test_compute_summary_basic():
    s = compute_summary(SAMPLE_RECORDS)
    assert s["min"] == 55.0
    assert s["max"] == 80.0
    assert s["avg"] == 66.25
    assert s["latest"] == 80.0
    assert s["count"] == 4


def test_compute_summary_empty_raises():
    with pytest.raises(SummaryError, match="No records"):
        compute_summary([])


def test_compute_summary_no_numeric_raises():
    records = [{"Week": "2024-04-07", "Value": None}]
    with pytest.raises(SummaryError, match="No numeric"):
        compute_summary(records)


def test_compute_summary_skips_non_numeric():
    records = [
        {"Week": "2024-04-07", "Value": "bad"},
        {"Week": "2024-04-14", "Value": "50"},
    ]
    s = compute_summary(records)
    assert s["count"] == 1
    assert s["latest"] == 50.0


def test_compute_summary_single_record():
    s = compute_summary([{"Value": "42"}])
    assert s["min"] == s["max"] == s["avg"] == s["latest"] == 42.0


def test_format_summary_contains_fields():
    s = compute_summary(SAMPLE_RECORDS)
    out = format_summary(s, commodity="CORN", unit="%")
    assert "CORN" in out
    assert "66.25%" in out
    assert "55.0%" in out
    assert "80.0%" in out
    assert "Count" in out


def test_format_summary_no_commodity():
    s = compute_summary(SAMPLE_RECORDS)
    out = format_summary(s)
    assert out.startswith("Summary")
    assert "CORN" not in out
