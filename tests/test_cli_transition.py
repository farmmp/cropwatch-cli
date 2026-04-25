"""CLI tests for the transition scan command."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from cropwatch.cli_transition import transition_group


@pytest.fixture()
def runner():
    return CliRunner()


def _rec(week: str, value: float) -> dict:
    return {
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": "CORN",
        "state_alpha": "US",
    }


_RECORDS = [
    _rec("2023-04-02", 10.0),
    _rec("2023-04-09", 25.0),
    _rec("2023-04-16", 18.0),
]


def _patch_client(records=None):
    if records is None:
        records = _RECORDS
    mock = MagicMock()
    mock.return_value.get_crop_progress.return_value = records
    return patch("cropwatch.cli_transition.UsdaClient", mock)


def _patch_key(key="testkey"):
    return patch("cropwatch.cli_transition.get_api_key", return_value=key)


def test_scan_success(runner):
    with _patch_key(), _patch_client():
        result = runner.invoke(
            transition_group, ["scan", "--commodity", "CORN", "--year", "2023"]
        )
    assert result.exit_code == 0
    assert "CORN" in result.output
    assert "Week Ending" in result.output


def test_scan_no_api_key(runner):
    with _patch_key(key=None):
        result = runner.invoke(
            transition_group, ["scan", "--commodity", "CORN"]
        )
    assert result.exit_code != 0
    assert "API key" in result.output or "API key" in (result.stderr or "")


def test_scan_api_error(runner):
    from cropwatch.usda_client import UsdaClientError

    mock = MagicMock()
    mock.return_value.get_crop_progress.side_effect = UsdaClientError("boom")
    with _patch_key(), patch("cropwatch.cli_transition.UsdaClient", mock):
        result = runner.invoke(
            transition_group, ["scan", "--commodity", "CORN"]
        )
    assert result.exit_code != 0


def test_scan_no_data_raises(runner):
    with _patch_key(), _patch_client(records=[]):
        result = runner.invoke(
            transition_group, ["scan", "--commodity", "CORN"]
        )
    assert result.exit_code != 0


def test_scan_with_threshold(runner):
    with _patch_key(), _patch_client():
        result = runner.invoke(
            transition_group,
            ["scan", "--commodity", "CORN", "--threshold", "5.0"],
        )
    assert result.exit_code == 0
    assert "▲" in result.output or "▼" in result.output or "─" in result.output


def test_scan_with_state(runner):
    records = [
        {"week_ending": "2023-04-02", "Value": "12.0", "commodity_desc": "CORN", "state_alpha": "IA"},
        {"week_ending": "2023-04-09", "Value": "30.0", "commodity_desc": "CORN", "state_alpha": "IA"},
    ]
    mock = MagicMock()
    mock.return_value.get_crop_progress.return_value = records
    with _patch_key(), patch("cropwatch.cli_transition.UsdaClient", mock):
        result = runner.invoke(
            transition_group,
            ["scan", "--commodity", "CORN", "--state", "IA"],
        )
    assert result.exit_code == 0
    assert "IA" in result.output
