"""Tests for cli_moving_avg."""
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from cropwatch.cli_moving_avg import movavg_group
from cropwatch.usda_client import UsdaClientError
from cropwatch.moving_avg import MovingAvgError


@pytest.fixture
def runner():
    return CliRunner()


def _patch_client(records):
    m = MagicMock()
    m.return_value.get_crop_progress.return_value = records
    return patch("cropwatch.cli_moving_avg.UsdaClient", m)


def _patch_key(key="testkey"):
    return patch("cropwatch.cli_moving_avg.get_api_key", return_value=key)


def _rec(week, value):
    return {
        "commodity_desc": "CORN",
        "statisticcat_desc": "PROGRESS",
        "unit_desc": "PCT",
        "week_ending": week,
        "Value": str(value),
    }


def test_show_movavg_success(runner):
    records = [_rec(f"2024-0{i}-01", i * 10) for i in range(1, 5)]
    with _patch_key(), _patch_client(records):
        result = runner.invoke(movavg_group, ["show", "--commodity", "CORN"])
    assert result.exit_code == 0
    assert "Moving Average" in result.output


def test_show_movavg_no_api_key(runner):
    with patch("cropwatch.cli_moving_avg.get_api_key", return_value=None):
        result = runner.invoke(movavg_group, ["show"])
    assert result.exit_code != 0
    assert "No API key" in result.output


def test_show_movavg_api_error(runner):
    m = MagicMock()
    m.return_value.get_crop_progress.side_effect = UsdaClientError("fail")
    with _patch_key(), patch("cropwatch.cli_moving_avg.UsdaClient", m):
        result = runner.invoke(movavg_group, ["show"])
    assert result.exit_code != 0
    assert "API error" in result.output


def test_show_movavg_no_data(runner):
    with _patch_key(), _patch_client([]):
        result = runner.invoke(movavg_group, ["show"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_show_movavg_state_label(runner):
    records = [_rec("2024-01-01", 50)]
    with _patch_key(), _patch_client(records):
        result = runner.invoke(movavg_group, ["show", "--state", "IA"])
    assert "IA" in result.output
