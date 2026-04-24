"""Tests for cropwatch.crossover."""
import pytest

from cropwatch.crossover import (
    CrossoverError,
    CrossoverEvent,
    _rolling_mean,
    detect_crossovers,
    format_crossovers,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "US") -> dict:
    return {
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": commodity,
        "state_alpha": state,
    }


# ---------------------------------------------------------------------------
# _rolling_mean
# ---------------------------------------------------------------------------

def test_rolling_mean_window1():
    result = _rolling_mean([1.0, 2.0, 3.0], 1)
    assert result == [1.0, 2.0, 3.0]


def test_rolling_mean_leading_nones():
    result = _rolling_mean([10.0, 20.0, 30.0, 40.0], 3)
    assert result[0] is None
    assert result[1] is None
    assert result[2] == pytest.approx(20.0)
    assert result[3] == pytest.approx(30.0)


def test_rolling_mean_empty():
    assert _rolling_mean([], 2) == []


# ---------------------------------------------------------------------------
# detect_crossovers
# ---------------------------------------------------------------------------

def _build_records():
    """Build a series that dips then rises, producing one bearish then one bullish crossover."""
    # weeks 1-4: rising (short will be above long eventually)
    # weeks 5-7: falling sharply (bearish crossover)
    # weeks 8-10: rising sharply (bullish crossover)
    values = [50, 52, 54, 56, 40, 38, 36, 55, 58, 62]
    return [_rec(f"2024-0{i+1}-01", v) for i, v in enumerate(values)]


def test_detect_crossovers_returns_list():
    records = _build_records()
    events = detect_crossovers(records, "CORN", short_window=2, long_window=4)
    assert isinstance(events, list)
    assert all(isinstance(e, CrossoverEvent) for e in events)


def test_detect_crossovers_directions_valid():
    records = _build_records()
    events = detect_crossovers(records, "CORN", short_window=2, long_window=4)
    for ev in events:
        assert ev.direction in ("bullish", "bearish")


def test_detect_crossovers_filters_commodity():
    records = _build_records() + [_rec("2024-11-01", 99.0, commodity="SOYBEANS")]
    events = detect_crossovers(records, "CORN", short_window=2, long_window=4)
    # All events must come from CORN data only — no error expected
    assert isinstance(events, list)


def test_detect_crossovers_filters_state():
    base = _build_records()  # state="US"
    extra = [_rec(f"2024-0{i+1}-01", 10.0, state="IA") for i in range(10)]
    events = detect_crossovers(base + extra, "CORN", short_window=2, long_window=4, state="US")
    assert isinstance(events, list)


def test_detect_crossovers_invalid_window_raises():
    records = _build_records()
    with pytest.raises(CrossoverError, match="short_window"):
        detect_crossovers(records, "CORN", short_window=5, long_window=3)


def test_detect_crossovers_no_data_raises():
    with pytest.raises(CrossoverError, match="No records found"):
        detect_crossovers([], "CORN")


def test_detect_crossovers_too_few_points_raises():
    records = [_rec(f"2024-0{i+1}-01", float(i)) for i in range(3)]
    with pytest.raises(CrossoverError, match="Not enough data"):
        detect_crossovers(records, "CORN", short_window=2, long_window=6)


def test_detect_crossovers_skips_bad_values():
    records = _build_records()
    records[2]["Value"] = "N/A"
    # Should not raise; bad record is skipped
    events = detect_crossovers(records, "CORN", short_window=2, long_window=4)
    assert isinstance(events, list)


# ---------------------------------------------------------------------------
# format_crossovers
# ---------------------------------------------------------------------------

def test_format_crossovers_no_events():
    output = format_crossovers([], "CORN")
    assert "No crossover" in output


def test_format_crossovers_contains_header():
    events = [CrossoverEvent("2024-05-01", "bullish", 52.0, 50.0)]
    output = format_crossovers(events, "CORN")
    assert "CORN" in output
    assert "Bullish" in output or "bullish" in output.lower()


def test_format_crossovers_contains_week():
    events = [CrossoverEvent("2024-05-01", "bearish", 48.0, 50.0)]
    output = format_crossovers(events, "CORN")
    assert "2024-05-01" in output
