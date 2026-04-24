"""Tests for cropwatch.rebound."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from cropwatch.rebound import (
    ReboundError,
    ReboundResult,
    _extract_sorted,
    detect_rebounds,
    format_rebounds,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "US") -> dict:
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "week_ending": week,
        "Value": str(value),
    }


RECORDS = [
    _rec("2023-04-01", 10.0),
    _rec("2023-04-08", 20.0),
    _rec("2023-04-15", 15.0),  # dip
    _rec("2023-04-22", 25.0),  # rebound above 20
    _rec("2023-04-29", 22.0),
]


def test_extract_sorted_basic():
    series = _extract_sorted(RECORDS, "CORN", "US")
    assert len(series) == 5
    weeks = [w for w, _ in series]
    assert weeks == sorted(weeks)


def test_extract_sorted_filters_commodity():
    extra = RECORDS + [_rec("2023-05-06", 30.0, commodity="SOYBEANS")]
    series = _extract_sorted(extra, "CORN", "US")
    assert len(series) == 5


def test_extract_sorted_filters_state():
    extra = RECORDS + [_rec("2023-05-06", 30.0, state="IA")]
    series = _extract_sorted(extra, "CORN", "US")
    assert len(series) == 5


def test_detect_rebound_found():
    results = detect_rebounds(RECORDS, commodity="CORN", state="US", min_depth=2.0)
    assert len(results) == 1
    r = results[0]
    assert isinstance(r, ReboundResult)
    assert r.prior_value == 20.0
    assert r.dip_value == 15.0
    assert r.recover_value == 25.0
    assert r.depth == 5.0
    assert r.gain == 5.0


def test_detect_rebound_below_min_depth():
    """A small dip below min_depth threshold should not be reported."""
    records = [
        _rec("2023-04-01", 10.0),
        _rec("2023-04-08", 20.0),
        _rec("2023-04-15", 19.0),  # dip of 1 — below default 2.0
        _rec("2023-04-22", 25.0),
    ]
    results = detect_rebounds(records, commodity="CORN", state="US", min_depth=2.0)
    assert results == []


def test_detect_no_rebound_monotone():
    records = [_rec(f"2023-04-{i:02d}", float(i * 5)) for i in range(1, 8)]
    results = detect_rebounds(records, commodity="CORN", state="US", min_depth=1.0)
    assert results == []


def test_detect_too_few_points_raises():
    with pytest.raises(ReboundError, match="at least 3"):
        detect_rebounds(
            [_rec("2023-04-01", 10.0), _rec("2023-04-08", 20.0)],
            commodity="CORN",
            state="US",
        )


def test_format_rebounds_no_results():
    out = format_rebounds([], commodity="CORN", state="US")
    assert "No rebounds" in out


def test_format_rebounds_with_results():
    results = detect_rebounds(RECORDS, commodity="CORN", state="US", min_depth=2.0)
    out = format_rebounds(results, commodity="CORN", state="US")
    assert "Rebound" in out
    assert "20231408" in out or "20230408" in out or "20230422" in out
    assert "25.0" in out
