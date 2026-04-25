"""Tests for cropwatch.concentration."""
from __future__ import annotations

import pytest

from cropwatch.concentration import (
    ConcentrationError,
    _extract_keyed,
    compute_concentration,
    format_concentration,
)


def _rec(state: str, value: float, commodity: str = "CORN", week: str = "2023-06-04") -> dict:
    return {
        "commodity_desc": commodity,
        "week_ending": week,
        "state_alpha": state,
        "Value": str(value),
    }


@pytest.fixture()
def records():
    return [
        _rec("IA", 40.0),
        _rec("IL", 30.0),
        _rec("NE", 20.0),
        _rec("MN", 10.0),
    ]


def test_extract_keyed_basic(records):
    keyed = _extract_keyed(records, "CORN", "2023-06-04")
    assert set(keyed.keys()) == {"IA", "IL", "NE", "MN"}
    assert keyed["IA"] == 40.0


def test_extract_keyed_excludes_us():
    recs = [_rec("US", 100.0), _rec("IA", 50.0)]
    keyed = _extract_keyed(recs, "CORN", "2023-06-04")
    assert "US" not in keyed
    assert "IA" in keyed


def test_extract_keyed_filters_commodity(records):
    keyed = _extract_keyed(records, "SOYBEANS", "2023-06-04")
    assert keyed == {}


def test_extract_keyed_skips_bad_value():
    recs = [_rec("IA", 0.0), {"commodity_desc": "CORN", "week_ending": "2023-06-04", "state_alpha": "IL", "Value": "N/A"}]
    keyed = _extract_keyed(recs, "CORN", "2023-06-04")
    assert "IL" not in keyed


def test_compute_basic_hhi(records):
    result = compute_concentration(records, "CORN", "2023-06-04")
    # shares: IA=0.4, IL=0.3, NE=0.2, MN=0.1 => HHI = (40^2+30^2+20^2+10^2)/100 = 3000/100 = 30
    assert result.hhi == pytest.approx(30.0, rel=1e-3)


def test_compute_top_state(records):
    result = compute_concentration(records, "CORN", "2023-06-04")
    assert result.top_state == "IA"
    assert result.top_share == pytest.approx(0.4, rel=1e-3)


def test_compute_state_shares_sum_to_one(records):
    result = compute_concentration(records, "CORN", "2023-06-04")
    assert sum(result.state_shares.values()) == pytest.approx(1.0, rel=1e-3)


def test_compute_empty_raises():
    with pytest.raises(ConcentrationError, match="No data"):
        compute_concentration([], "CORN", "2023-06-04")


def test_compute_zero_total_raises():
    recs = [_rec("IA", 0.0), _rec("IL", 0.0)]
    with pytest.raises(ConcentrationError, match="zero"):
        compute_concentration(recs, "CORN", "2023-06-04")


def test_format_concentration_contains_hhi(records):
    result = compute_concentration(records, "CORN", "2023-06-04")
    text = format_concentration(result)
    assert "HHI" in text
    assert "IA" in text
    assert "CORN" in text
