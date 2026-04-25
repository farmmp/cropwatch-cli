"""Tests for cropwatch.cli_dominance."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from cropwatch.cli_dominance import dominance_group


def _rec(state: str, week: str, value: float) -> dict:
    return {
        "state_alpha": state,
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": "CORN",
        "short_desc": "CORN - PROGRESS PCT",
    }


_records = [
    _rec("IA", "2023-05-01", 80.0),
    _rec("IL", "2023-05-01", 70.0),
    _rec("IA", "2023-05-08", 75.0),
    _rec("IL", "2023-05-08", 85.0),
]


@pytest.fixture()
def runner():
    return CliRunner()


def _patch_client(return_value=None):
    return patch(
        "cropwatch.cli_dominance.UsdaClient.get_crop_progress",
        return_value=return_value or _records,
    )


def _patch_key(key="test-key"):
    return patch("cropwatch.cli_dominance.get_api_key", return_value=key)


def test_top_success(runner):
    with _patch_key(), _patch_client():
        result = runner.invoke(
            dominance_group,
            ["top", "--commodity", "CORN", "--attribute", "PROGRESS", "--year", "2023"],
        )
    assert result.exit_code == 0
    assert "IA" in result.output or "IL" in result.output


def test_top_no_api_key(runner):
    with _patch_key(key=None):
        result = runner.invoke(
            dominance_group,
            ["top", "--commodity", "CORN", "--attribute", "PROGRESS"],
        )
    assert result.exit_code != 0
    assert "no API key" in result.output


def test_top_api_error(runner):
    from cropwatch.usda_client import UsdaClientError

    with _patch_key(), patch(
        "cropwatch.cli_dominance.UsdaClient.get_crop_progress",
        side_effect=UsdaClientError("boom"),
    ):
        result = runner.invoke(
            dominance_group,
            ["top", "--commodity", "CORN", "--attribute", "PROGRESS"],
        )
    assert result.exit_code != 0
    assert "API error" in result.output


def test_top_no_matching_data(runner):
    with _patch_key(), _patch_client():
        result = runner.invoke(
            dominance_group,
            ["top", "--commodity", "WHEAT", "--attribute", "PROGRESS"],
        )
    assert result.exit_code != 0
    assert "Dominance error" in result.output


def test_top_respects_top_n(runner):
    with _patch_key(), _patch_client():
        result = runner.invoke(
            dominance_group,
            ["top", "--commodity", "CORN", "--attribute", "PROGRESS", "--top", "1"],
        )
    assert result.exit_code == 0
    # Only one state row should appear after the header/sep lines
    lines = [l for l in result.output.splitlines() if l.strip() and not l.startswith("-") and "State" not in l and "Dominance" not in l]
    assert len(lines) == 1
