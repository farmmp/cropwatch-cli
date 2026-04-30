"""Tests for cropwatch.compression."""
import pytest
from cropwatch.compression import (
    CompressionError,
    CompressionResult,
    _extract_sorted,
    compute_compression,
    format_compression,
)


def _rec(week, value, commodity="CORN", state="IA", unit="PCT EXCELLENT"):
    return {
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": commodity,
        "state_alpha": state,
        "unit_desc": unit,
    }


def _make_records(weeks, high_vals, low_vals, commodity="CORN", state="IA"):
    recs = []
    for w, h, l in zip(weeks, high_vals, low_vals):
        recs.append(_rec(w, h, commodity, state, "PCT EXCELLENT"))
        recs.append(_rec(w, l, commodity, state, "PCT POOR"))
    return recs


WEEKS = ["2024-05-01", "2024-05-08", "2024-05-15", "2024-05-22"]


def test_extract_sorted_basic():
    recs = [_rec("2024-05-01", 30), _rec("2024-05-08", 40)]
    out = _extract_sorted(recs, "CORN", "IA")
    assert len(out) == 2
    assert out[0]["week"] == "2024-05-01"


def test_extract_sorted_filters_commodity():
    recs = [_rec("2024-05-01", 30, commodity="SOYBEANS")]
    assert _extract_sorted(recs, "CORN", "IA") == []


def test_extract_sorted_filters_state():
    recs = [_rec("2024-05-01", 30, state="IL")]
    assert _extract_sorted(recs, "CORN", "IA") == []


def test_extract_sorted_skips_bad_value():
    recs = [_rec("2024-05-01", "N/A")]
    assert _extract_sorted(recs, "CORN", "IA") == []


def test_compute_compression_basic():
    # spreads: 30-10=20, 25-15=10, 20-18=2 → all compressing
    recs = _make_records(WEEKS[:3], [30, 25, 20], [10, 15, 18])
    results = compute_compression(recs, "CORN", "IA")
    assert len(results) == 2
    assert all(isinstance(r, CompressionResult) for r in results)
    assert all(r.delta < 0 for r in results)


def test_compute_compression_no_compression():
    # spreads widening: 10, 20, 30
    recs = _make_records(WEEKS[:3], [15, 25, 35], [5, 5, 5])
    results = compute_compression(recs, "CORN", "IA")
    assert results == []


def test_compute_compression_empty_raises():
    with pytest.raises(CompressionError, match="No records"):
        compute_compression([], "CORN", "IA")


def test_compute_compression_too_few_weeks_raises():
    recs = _make_records(WEEKS[:1], [30], [10])
    with pytest.raises(CompressionError, match="Not enough"):
        compute_compression(recs, "CORN", "IA")


def test_compute_compression_threshold():
    # spread changes: -10, -8 — only -10 passes threshold of -9
    recs = _make_records(WEEKS[:3], [30, 20, 12], [10, 10, 10])
    results = compute_compression(recs, "CORN", "IA", threshold=-9.0)
    assert len(results) == 1
    assert results[0].delta == -10.0


def test_format_compression_no_results():
    out = format_compression([], "CORN")
    assert "No spread compression" in out


def test_format_compression_with_results():
    recs = _make_records(WEEKS[:3], [30, 25, 20], [10, 15, 18])
    results = compute_compression(recs, "CORN", "IA")
    out = format_compression(results, "CORN")
    assert "CORN" in out
    assert "Week" in out
    assert "Delta" in out
    assert str(WEEKS[1]) in out
