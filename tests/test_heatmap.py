import pytest
from cropwatch.heatmap import build_heatmap, format_heatmap, HeatmapError, _heat_char

RECORDS = [
    {"commodity_desc": "CORN", "week_ending": "2024-05-05", "state_alpha": "IA", "Value": "72"},
    {"commodity_desc": "CORN", "week_ending": "2024-05-05", "state_alpha": "IL", "Value": "55"},
    {"commodity_desc": "CORN", "week_ending": "2024-05-05", "state_alpha": "NE", "Value": "90"},
    {"commodity_desc": "SOYBEANS", "week_ending": "2024-05-05", "state_alpha": "IA", "Value": "40"},
]


def test_heat_char_low():
    assert _heat_char(0, 0, 100) == " "


def test_heat_char_high():
    assert _heat_char(100, 0, 100) == "█"


def test_heat_char_uniform():
    ch = _heat_char(50, 50, 50)
    assert ch == "▒"


def test_build_heatmap_basic():
    result = build_heatmap(RECORDS, "CORN", "2024-05-05")
    assert result["IA"] == 72.0
    assert result["IL"] == 55.0
    assert result["NE"] == 90.0


def test_build_heatmap_filters_commodity():
    result = build_heatmap(RECORDS, "SOYBEANS", "2024-05-05")
    assert list(result.keys()) == ["IA"]


def test_build_heatmap_no_data_raises():
    with pytest.raises(HeatmapError):
        build_heatmap(RECORDS, "WHEAT", "2024-05-05")


def test_build_heatmap_wrong_week_raises():
    with pytest.raises(HeatmapError):
        build_heatmap(RECORDS, "CORN", "2024-01-01")


def test_format_heatmap_contains_states():
    sv = {"IA": 72.0, "IL": 55.0, "NE": 90.0}
    out = format_heatmap(sv, title="CORN Progress")
    assert "IA" in out
    assert "IL" in out
    assert "NE" in out


def test_format_heatmap_contains_range():
    sv = {"IA": 72.0, "IL": 55.0}
    out = format_heatmap(sv)
    assert "Range:" in out
    assert "55.0" in out
    assert "72.0" in out


def test_format_heatmap_empty_raises():
    with pytest.raises(HeatmapError):
        format_heatmap({})
