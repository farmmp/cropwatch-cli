"""Tests for cropwatch.export module."""

import json
import os

import pytest

from cropwatch.export import ExportError, export_data, write_export

SAMPLE = [
    {"commodity_desc": "CORN", "week_ending": "2024-05-05", "Value": "45", "short_desc": "PLANTED"},
    {"commodity_desc": "CORN", "week_ending": "2024-05-12", "Value": "68", "short_desc": "PLANTED"},
]


def test_export_json_returns_valid_json():
    result = export_data(SAMPLE, "json")
    parsed = json.loads(result)
    assert len(parsed) == 2
    assert parsed[0]["commodity_desc"] == "CORN"


def test_export_csv_contains_header():
    result = export_data(SAMPLE, "csv")
    lines = result.strip().splitlines()
    assert lines[0] == "commodity_desc,week_ending,Value,short_desc"


def test_export_csv_row_count():
    result = export_data(SAMPLE, "csv")
    lines = result.strip().splitlines()
    # header + 2 data rows
    assert len(lines) == 3


def test_export_csv_values():
    result = export_data(SAMPLE, "csv")
    assert "45" in result
    assert "68" in result


def test_unsupported_format_raises():
    with pytest.raises(ExportError, match="Unsupported format"):
        export_data(SAMPLE, "xml")


def test_empty_records_raises():
    with pytest.raises(ExportError, match="No data"):
        export_data([], "csv")


def test_write_export_creates_file(tmp_path):
    out = tmp_path / "report.csv"
    write_export(SAMPLE, "csv", str(out))
    assert out.exists()
    content = out.read_text()
    assert "CORN" in content


def test_write_export_json_file(tmp_path):
    out = tmp_path / "report.json"
    write_export(SAMPLE, "json", str(out))
    parsed = json.loads(out.read_text())
    assert isinstance(parsed, list)
    assert len(parsed) == 2
