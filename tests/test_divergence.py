"""Tests for cropwatch.divergence."""
import pytest
from cropwatch.divergence import (
    DivergenceError,
    DivergenceResult,
    compute_divergence,
    format_divergence,
    _extract_keyed,
)


def _rec(state: str, week: str, value: float) -> dict:
    return {
        "commodity_desc": "CORN",
        "short_desc": "CORN - PROGRESS, MEASURED IN PCT EMERGED",
        "state_alpha": state,
        "week_ending": week,
        "Value": str(value),
    }


@pytest.fixture
def records():
    return [
        _rec("IA", "2023-05-07", 30.0),
        _rec("IA", "2023-05-14", 55.0),
        _rec("IA", "2023-05-21", 80.0),
        _rec("IL", "2023-05-07", 20.0),
        _rec("IL", "2023-05-14", 45.0),
        _rec("IL", "2023-05-21", 70.0),
    ]


def test_compute_basic_length(records):
    results = compute_divergence(
        records,
        label="CORN - PROGRESS, MEASURED IN PCT EMERGED",
        commodity="CORN",
        state_a="IA",
        state_b="IL",
    )
    assert len(results) == 3


def test_compute_basic_values(records):
    results = compute_divergence(
        records,
        label="CORN - PROGRESS, MEASURED IN PCT EMERGED",
        commodity="CORN",
        state_a="IA",
        state_b="IL",
    )
    assert results[0].week_end == "2023-05-07"
    assert results[0].value_a == 30.0
    assert results[0].value_b == 20.0
    assert results[0].delta == 10.0


def test_compute_sorted_by_week(records):
    results = compute_divergence(
        records,
        label="CORN - PROGRESS, MEASURED IN PCT EMERGED",
        commodity="CORN",
        state_a="IA",
        state_b="IL",
    )
    weeks = [r.week_end for r in results]
    assert weeks == sorted(weeks)


def test_compute_negative_delta(records):
    results = compute_divergence(
        records,
        label="CORN - PROGRESS, MEASURED IN PCT EMERGED",
        commodity="CORN",
        state_a="IL",
        state_b="IA",
    )
    assert all(r.delta < 0 for r in results)


def test_empty_records_raises():
    with pytest.raises(DivergenceError, match="No records"):
        compute_divergence([], "lbl", "CORN", "IA", "IL")


def test_no_overlap_raises(records):
    """State with no data should cause DivergenceError."""
    with pytest.raises(DivergenceError, match="No overlapping weeks"):
        compute_divergence(
            records,
            label="CORN - PROGRESS, MEASURED IN PCT EMERGED",
            commodity="CORN",
            state_a="IA",
            state_b="MN",
        )


def test_extract_keyed_skips_bad_values(records):
    bad = records + [
        {
            "commodity_desc": "CORN",
            "short_desc": "CORN - PROGRESS, MEASURED IN PCT EMERGED",
            "state_alpha": "IA",
            "week_ending": "2023-05-28",
            "Value": "(D)",
        }
    ]
    series = _extract_keyed(
        bad,
        "CORN - PROGRESS, MEASURED IN PCT EMERGED",
        "CORN",
        "IA",
    )
    assert "2023-05-28" not in series
    assert len(series) == 3


def test_format_divergence_contains_states(records):
    results = compute_divergence(
        records,
        label="CORN - PROGRESS, MEASURED IN PCT EMERGED",
        commodity="CORN",
        state_a="IA",
        state_b="IL",
    )
    output = format_divergence(results, "IA", "IL")
    assert "IA" in output
    assert "IL" in output
    assert "Delta" in output


def test_format_divergence_row_count(records):
    results = compute_divergence(
        records,
        label="CORN - PROGRESS, MEASURED IN PCT EMERGED",
        commodity="CORN",
        state_a="IA",
        state_b="IL",
    )
    output = format_divergence(results, "IA", "IL")
    # header + separator + 3 data rows
    assert len(output.strip().splitlines()) == 5
