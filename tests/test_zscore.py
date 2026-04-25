"""Tests for cropwatch.zscore."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from cropwatch.zscore import (
    ZScoreError,
    ZScoreResult,
    _mean_std,
    compute_zscores,
    format_zscores,
)


def _rec(week: str, value: str, commodity: str = "CORN",
         short_desc: str = "CORN - PROGRESS", state: str = "IOWA") -> dict:
    return {
        "week_ending": week,
        "commodity_desc": commodity,
        "short_desc": short_desc,
        "state_name": state,
        "Value": value,
    }


RECORDS = [
    _rec("2023-10-01", "10"),
    _rec("2023-10-08", "20"),
    _rec("2023-10-15", "30"),
    _rec("2023-10-22", "40"),
    _rec("2023-10-29", "90"),  # outlier
]


# --- _mean_std ---

def test_mean_std_basic():
    mean, std = _mean_std([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert abs(mean - 5.0) < 1e-9
    assert abs(std - 2.0) < 1e-9


def test_mean_std_empty():
    mean, std = _mean_std([])
    assert mean == 0.0
    assert std == 0.0


def test_mean_std_uniform():
    _, std = _mean_std([5.0, 5.0, 5.0])
    assert std == 0.0


# --- compute_zscores ---

def test_compute_basic_length():
    results = compute_zscores(RECORDS, commodity="CORN", attribute="CORN - PROGRESS")
    assert len(results) == 5


def test_compute_sorted_by_abs_zscore():
    results = compute_zscores(RECORDS, commodity="CORN", attribute="CORN - PROGRESS")
    abs_scores = [abs(r.zscore) for r in results]
    assert abs_scores == sorted(abs_scores, reverse=True)


def test_compute_outlier_first():
    results = compute_zscores(RECORDS, commodity="CORN", attribute="CORN - PROGRESS")
    assert results[0].value == pytest.approx(90.0)


def test_compute_filters_state():
    extra = _rec("2023-10-01", "99", state="ILLINOIS")
    results = compute_zscores(
        RECORDS + [extra], commodity="CORN", attribute="CORN - PROGRESS", state="IOWA"
    )
    assert all(r.value != 99.0 for r in results)


def test_compute_skips_bad_values():
    bad = _rec("2023-11-01", "(D)")  # non-numeric USDA suppressed value
    results = compute_zscores(
        RECORDS + [bad], commodity="CORN", attribute="CORN - PROGRESS"
    )
    assert len(results) == 5


def test_compute_empty_raises():
    with pytest.raises(ZScoreError):
        compute_zscores([], commodity="CORN", attribute="CORN - PROGRESS")


def test_compute_too_few_raises():
    with pytest.raises(ZScoreError):
        compute_zscores(
            [_rec("2023-10-01", "50")], commodity="CORN", attribute="CORN - PROGRESS"
        )


def test_compute_uniform_values_zero_zscore():
    uniform = [_rec(f"2023-10-0{i}", "50") for i in range(1, 5)]
    results = compute_zscores(uniform, commodity="CORN", attribute="CORN - PROGRESS")
    assert all(r.zscore == 0.0 for r in results)


# --- format_zscores ---

def test_format_contains_header():
    results = compute_zscores(RECORDS, commodity="CORN", attribute="CORN - PROGRESS")
    output = format_zscores(results)
    assert "Week" in output
    assert "Z-Score" in output


def test_format_top_n_limits_rows():
    results = compute_zscores(RECORDS, commodity="CORN", attribute="CORN - PROGRESS")
    output = format_zscores(results, top_n=2)
    data_lines = [l for l in output.splitlines() if l and not l.startswith("-") and "Week" not in l]
    assert len(data_lines) == 2
