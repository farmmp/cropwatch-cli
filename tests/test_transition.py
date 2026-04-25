"""Unit tests for cropwatch.transition."""
import pytest

from cropwatch.transition import (
    TransitionError,
    TransitionEvent,
    _extract_sorted,
    detect_transitions,
    format_transitions,
)


def _rec(week: str, value: float, commodity: str = "CORN", state: str = "US") -> dict:
    return {
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": commodity,
        "state_alpha": state,
    }


BASE = [
    _rec("2023-04-02", 10.0),
    _rec("2023-04-09", 20.0),
    _rec("2023-04-16", 15.0),
    _rec("2023-04-23", 15.0),
]


def test_extract_sorted_basic():
    result = _extract_sorted(BASE, "CORN", "US")
    assert len(result) == 4
    assert result[0] == ("2023-04-02", 10.0)


def test_extract_sorted_filters_commodity():
    mixed = BASE + [_rec("2023-04-02", 99.0, commodity="SOYBEANS")]
    result = _extract_sorted(mixed, "CORN", "US")
    assert len(result) == 4


def test_extract_sorted_filters_state():
    mixed = BASE + [_rec("2023-04-02", 99.0, state="IA")]
    result = _extract_sorted(mixed, "CORN", "US")
    assert len(result) == 4


def test_extract_sorted_skips_bad_value():
    bad = BASE + [{"week_ending": "2023-04-30", "Value": "(D)", "commodity_desc": "CORN", "state_alpha": "US"}]
    result = _extract_sorted(bad, "CORN", "US")
    assert len(result) == 4


def test_detect_transitions_basic():
    result = detect_transitions(BASE, "CORN", "US")
    assert len(result.events) == 3


def test_detect_transitions_directions():
    result = detect_transitions(BASE, "CORN", "US")
    assert result.events[0].direction == "up"
    assert result.events[1].direction == "down"
    assert result.events[2].direction == "flat"


def test_detect_transitions_magnitudes():
    result = detect_transitions(BASE, "CORN", "US")
    assert result.events[0].magnitude == pytest.approx(10.0)
    assert result.events[1].magnitude == pytest.approx(5.0)
    assert result.events[2].magnitude == pytest.approx(0.0)


def test_detect_transitions_dominant():
    result = detect_transitions(BASE, "CORN", "US")
    # up=1, down=1, flat=1 — any is valid; just check it's one of the three
    assert result.dominant_direction in {"up", "down", "flat"}


def test_detect_transitions_avg_magnitude():
    result = detect_transitions(BASE, "CORN", "US")
    expected = (10.0 + 5.0 + 0.0) / 3
    assert result.avg_magnitude == pytest.approx(expected, rel=1e-4)


def test_detect_transitions_threshold_flattens():
    result = detect_transitions(BASE, "CORN", "US", threshold=5.0)
    # delta=10 > 5 → up; delta=-5 == 5 → flat; delta=0 → flat
    assert result.events[0].direction == "up"
    assert result.events[1].direction == "flat"


def test_detect_empty_raises():
    with pytest.raises(TransitionError):
        detect_transitions([], "CORN", "US")


def test_detect_too_few_raises():
    with pytest.raises(TransitionError):
        detect_transitions([_rec("2023-04-02", 10.0)], "CORN", "US")


def test_format_transitions_contains_header():
    result = detect_transitions(BASE, "CORN", "US")
    output = format_transitions(result)
    assert "CORN" in output
    assert "US" in output
    assert "Week Ending" in output


def test_format_transitions_row_count():
    result = detect_transitions(BASE, "CORN", "US")
    output = format_transitions(result)
    data_lines = [l for l in output.splitlines() if "2023" in l]
    assert len(data_lines) == 3
