"""Tests for cli_correlation."""
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from cropwatch.cli_correlation import correlation_group
from cropwatch.usda_client import UsdaClientError


@pytest.fixture
def runner():
    return CliRunner()


def _rec(week, val_a, val_b, comm_a="CORN", comm_b="SOYBEANS"):
    base = {"unit_desc": "PCT", "statisticcat_desc": "PROGRESS", "week_ending": week}
    return [
        {**base, "commodity_desc": comm_a, "Value": str(val_a)},
        {**base, "commodity_desc": comm_b, "Value": str(val_b)},
    ]


def _all_records():
    rows = []
    for i in range(1, 8):
        rows.extend(_rec(f"2024-0{i}-01", i * 10, i * 9))
    return rows


def _patch_key(key="testkey"):
    return patch("cropwatch.cli_correlation.get_api_key", return_value=key)


def _patch_client(records):
    m = MagicMock()
    m.return_value.get_crop_progress.return_value = records
    return patch("cropwatch.cli_correlation.UsdaClient", m)


def test_run_correlation_success(runner):
    with _patch_key(), _patch_client(_all_records()):
        result = runner.invoke(
            correlation_group,
            ["run", "--commodity-a", "CORN", "--commodity-b", "SOYBEANS"],
        )
    assert result.exit_code == 0
    assert "Correlation" in result.output


def test_run_correlation_no_api_key(runner):
    with patch("cropwatch.cli_correlation.get_api_key", return_value=None):
        result = runner.invoke(correlation_group, ["run"])
    assert result.exit_code != 0
    assert "No API key" in result.output


def test_run_correlation_api_error(runner):
    m = MagicMock()
    m.return_value.get_crop_progress.side_effect = UsdaClientError("boom")
    with _patch_key(), patch("cropwatch.cli_correlation.UsdaClient", m):
        result = runner.invoke(correlation_group, ["run"])
    assert result.exit_code != 0
    assert "API error" in result.output


def test_run_correlation_no_data(runner):
    with _patch_key(), _patch_client([]):
        result = runner.invoke(correlation_group, ["run"])
    assert result.exit_code != 0
    assert "Error" in result.output
