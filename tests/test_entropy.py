"""Tests for cropwatch.entropy."""
import math
import pytest

from cropwatch.entropy import (
    EntropyError,
    EntropyResult,
    _extract_keyed,
    compute_entropy,
    format_entropy,
)


def _rec(state: str, value, commodity: str = "CORN", week: str = "2024-06-01") -> dict:
    return {
        "commodity_desc": commodity,
        "week_ending": week,
        "state_alpha": state,
        "Value": str(value),
    }


# ---------------------------------------------------------------------------
# _extract_keyed
# ---------------------------------------------------------------------------

def test_extract_keyed_basic():
    records = [_rec("IA", 40), _rec("IL", 60)]
    result = _extract_keyed(records, "CORN", "2024-06-01")
    assert result == {"IA": 40.0, "IL": 60.0}


def test_extract_keyed_excludes_us():
    records = [_rec("US", 100), _rec("IA", 40)]
    result = _extract_keyed(records, "CORN", "2024-06-01")
    assert "US" not in result
    assert "IA" in result


def test_extract_keyed_filters_commodity():
    records = [_rec("IA", 40, commodity="CORN"), _rec("IA", 50, commodity="SOYBEANS")]
    result = _extract_keyed(records, "CORN", "2024-06-01")
    assert result == {"IA": 40.0}


def test_extract_keyed_skips_bad_value():
    records = [_rec("IA", "N/A"), _rec("IL", 60)]
    result = _extract_keyed(records, "CORN", "2024-06-01")
    assert "IA" not in result
    assert result["IL"] == 60.0


def test_extract_keyed_skips_negative():
    records = [_rec("IA", -5), _rec("IL", 60)]
    result = _extract_keyed(records, "CORN", "2024-06-01")
    assert "IA" not in result


# ---------------------------------------------------------------------------
# compute_entropy
# ---------------------------------------------------------------------------

def test_compute_entropy_basic():
    # Two equal states → max entropy = 1 bit, normalised = 1.0
    records = [_rec("IA", 50), _rec("IL", 50)]
    res = compute_entropy(records, "CORN", "2024-06-01")
    assert isinstance(res, EntropyResult)
    assert res.entropy == pytest.approx(1.0, abs=1e-4)
    assert res.normalized_entropy == pytest.approx(1.0, abs=1e-4)


def test_compute_entropy_concentrated():
    # One dominant state → low normalised entropy
    records = [_rec("IA", 99), _rec("IL", 1)]
    res = compute_entropy(records, "CORN", "2024-06-01")
    assert res.normalized_entropy < 0.5


def test_compute_entropy_single_state():
    records = [_rec("IA", 100)]
    res = compute_entropy(records, "CORN", "2024-06-01")
    # log2(1) == 0, so entropy == 0
    assert res.entropy == 0.0
    assert res.max_entropy == 0.0
    assert res.normalized_entropy == 0.0


def test_compute_entropy_empty_raises():
    with pytest.raises(EntropyError, match="No records"):
        compute_entropy([], "CORN", "2024-06-01")


def test_compute_entropy_no_matching_raises():
    records = [_rec("IA", 50, commodity="SOYBEANS")]
    with pytest.raises(EntropyError, match="No valid state data"):
        compute_entropy(records, "CORN", "2024-06-01")


def test_compute_entropy_all_zeros_raises():
    records = [_rec("IA", 0), _rec("IL", 0)]
    with pytest.raises(EntropyError, match="zero"):
        compute_entropy(records, "CORN", "2024-06-01")


# ---------------------------------------------------------------------------
# format_entropy
# ---------------------------------------------------------------------------

def test_format_entropy_contains_header():
    records = [_rec("IA", 50), _rec("IL", 50)]
    res = compute_entropy(records, "CORN", "2024-06-01")
    out = format_entropy(res)
    assert "CORN" in out
    assert "2024-06-01" in out


def test_format_entropy_shows_bits():
    records = [_rec("IA", 50), _rec("IL", 50)]
    res = compute_entropy(records, "CORN", "2024-06-01")
    out = format_entropy(res)
    assert "bits" in out


def test_format_entropy_uniform_label():
    records = [_rec("IA", 50), _rec("IL", 50)]
    res = compute_entropy(records, "CORN", "2024-06-01")
    out = format_entropy(res)
    assert "uniform" in out
