"""Tests for cropwatch.recovery."""
import pytest
from cropwatch.recovery import (
    RecoveryError,
    RecoveryResult,
    _extract_sorted,
    detect_recoveries,
    format_recoveries,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "IA") -> dict:
    return {
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": commodity,
        "state_alpha": state,
    }


# ── _extract_sorted ──────────────────────────────────────────────────────────

def test_extract_sorted_basic():
    records = [_rec("2023-05-14", 50), _rec("2023-05-07", 40)]
    result = _extract_sorted(records, "CORN", "IA")
    assert [r["value"] for r in result] == [40.0, 50.0]


def test_extract_sorted_filters_commodity():
    records = [_rec("2023-05-07", 40, commodity="SOYBEANS"), _rec("2023-05-07", 55)]
    result = _extract_sorted(records, "CORN", "IA")
    assert len(result) == 1
    assert result[0]["value"] == 55.0


def test_extract_sorted_filters_state():
    records = [_rec("2023-05-07", 40, state="IL"), _rec("2023-05-07", 55, state="IA")]
    result = _extract_sorted(records, "CORN", "IA")
    assert len(result) == 1
    assert result[0]["value"] == 55.0


def test_extract_sorted_skips_bad_value():
    records = [_rec("2023-05-07", 40), {"week_ending": "2023-05-14", "Value": "(D)", "commodity_desc": "CORN", "state_alpha": "IA"}]
    result = _extract_sorted(records, "CORN", "IA")
    assert len(result) == 1


# ── detect_recoveries ────────────────────────────────────────────────────────

def test_detect_too_few_raises():
    records = [_rec("2023-05-07", 40), _rec("2023-05-14", 35)]
    with pytest.raises(RecoveryError):
        detect_recoveries(records, "CORN", "IA")


def test_detect_finds_recovery():
    records = [
        _rec("2023-05-07", 60),
        _rec("2023-05-14", 50),  # drawdown of -10
        _rec("2023-05-21", 55),  # recovery of +5
    ]
    results = detect_recoveries(records, "CORN", "IA", min_drawdown=2.0, min_recovery=1.0)
    assert len(results) == 1
    r = results[0]
    assert r.prior_value == pytest.approx(60.0)
    assert r.trough_value == pytest.approx(50.0)
    assert r.recovery_value == pytest.approx(55.0)
    assert r.drawdown == pytest.approx(-10.0)
    assert r.recovery_gain == pytest.approx(5.0)
    assert r.net_change == pytest.approx(-5.0)


def test_detect_no_recovery_when_gain_too_small():
    records = [
        _rec("2023-05-07", 60),
        _rec("2023-05-14", 50),
        _rec("2023-05-21", 50.5),  # gain only 0.5, below min_recovery=1.0
    ]
    results = detect_recoveries(records, "CORN", "IA", min_drawdown=2.0, min_recovery=1.0)
    assert results == []


def test_detect_no_recovery_when_drawdown_too_small():
    records = [
        _rec("2023-05-07", 60),
        _rec("2023-05-14", 59),   # drawdown only -1, below min_drawdown=2.0
        _rec("2023-05-21", 65),
    ]
    results = detect_recoveries(records, "CORN", "IA", min_drawdown=2.0, min_recovery=1.0)
    assert results == []


def test_detect_multiple_recoveries():
    records = [
        _rec("2023-04-30", 70),
        _rec("2023-05-07", 60),
        _rec("2023-05-14", 65),
        _rec("2023-05-21", 55),
        _rec("2023-05-28", 62),
    ]
    results = detect_recoveries(records, "CORN", "IA", min_drawdown=2.0, min_recovery=1.0)
    assert len(results) == 2


# ── format_recoveries ────────────────────────────────────────────────────────

def test_format_no_results():
    out = format_recoveries([], "CORN")
    assert "No recovery" in out


def test_format_contains_header():
    r = RecoveryResult(
        week_ending="2023-05-21",
        prior_value=60.0,
        trough_value=50.0,
        recovery_value=55.0,
        drawdown=-10.0,
        recovery_gain=5.0,
        net_change=-5.0,
    )
    out = format_recoveries([r], "CORN")
    assert "CORN" in out
    assert "2023-05-21" in out
    assert "60.0" in out
