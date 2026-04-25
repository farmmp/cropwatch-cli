"""Integration tests for the leadlag CLI command group."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from cropwatch.cli_leadlag import leadlag_group


@pytest.fixture()
def runner():
    return CliRunner()


def _rec(commodity: str, week: str, value: float, state: str = "US") -> dict:
    return {
        "commodity_desc": commodity,
        "week_ending": week,
        "Value": str(value),
        "state_alpha": state,
    }


def _corn_records():
    weeks = [f"2023-0{i}-01" for i in range(1, 7)]
    return [_rec("CORN", w, (i + 1) * 10) for i, w in enumerate(weeks)]


def _soy_records():
    weeks = [f"2023-0{i}-01" for i in range(1, 7)]
    return [_rec("SOYBEANS", w, (i + 1) * 8) for i, w in enumerate(weeks)]


def _patch_client(corn, soy):
    """Patch UsdaClient.get_crop_progress to return corn then soy records."""
    call_count = {"n": 0}

    def _side_effect(**kwargs):
        call_count["n"] += 1
        return corn if call_count["n"] == 1 else soy

    return patch(
        "cropwatch.cli_leadlag.UsdaClient.get_crop_progress",
        side_effect=_side_effect,
    )


def _patch_key(value="testkey"):
    return patch("cropwatch.cli_leadlag.get_api_key", return_value=value)


def test_compare_success(runner):
    with _patch_key(), _patch_client(_corn_records(), _soy_records()):
        result = runner.invoke(
            leadlag_group,
            ["compare", "--commodity-a", "CORN", "--commodity-b", "SOYBEANS"],
        )
    assert result.exit_code == 0
    assert "CORN" in result.output
    assert "SOYBEANS" in result.output
    assert "Correlation" in result.output


def test_compare_no_api_key(runner):
    with _patch_key(None):
        result = runner.invoke(
            leadlag_group,
            ["compare", "--commodity-a", "CORN", "--commodity-b", "SOYBEANS"],
        )
    assert result.exit_code != 0
    assert "No API key" in result.output


def test_compare_api_error(runner):
    from cropwatch.usda_client import UsdaClientError

    with _patch_key(), patch(
        "cropwatch.cli_leadlag.UsdaClient.get_crop_progress",
        side_effect=UsdaClientError("timeout"),
    ):
        result = runner.invoke(
            leadlag_group,
            ["compare", "--commodity-a", "CORN", "--commodity-b", "SOYBEANS"],
        )
    assert result.exit_code != 0
    assert "timeout" in result.output


def test_compare_insufficient_data(runner):
    """Only one record per commodity → LeadLagError surfaced as ClickException."""
    with _patch_key(), _patch_client(
        [_rec("CORN", "2023-01-01", 10)],
        [_rec("SOYBEANS", "2023-01-01", 8)],
    ):
        result = runner.invoke(
            leadlag_group,
            ["compare", "--commodity-a", "CORN", "--commodity-b", "SOYBEANS"],
        )
    assert result.exit_code != 0


def test_compare_max_lag_option(runner):
    with _patch_key(), _patch_client(_corn_records(), _soy_records()):
        result = runner.invoke(
            leadlag_group,
            [
                "compare",
                "--commodity-a", "CORN",
                "--commodity-b", "SOYBEANS",
                "--max-lag", "2",
            ],
        )
    assert result.exit_code == 0
    assert "±2 weeks" in result.output
