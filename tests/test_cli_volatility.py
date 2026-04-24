"""Integration tests for the volatility CLI commands."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cropwatch.cli_volatility import volatility_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _rec(value: float, week: str = "2023-04-01") -> dict:
    return {
        "commodity_desc": "CORN",
        "short_desc": "CORN - PROGRESS, MEASURED IN PCT PLANTED",
        "state_alpha": "US",
        "year": 2023,
        "week_ending": week,
        "Value": str(value),
    }


FAKE_RECORDS = [
    _rec(10.0, "2023-04-01"),
    _rec(25.0, "2023-04-08"),
    _rec(40.0, "2023-04-15"),
]


def _patch_client(records=FAKE_RECORDS):
    mock = MagicMock()
    mock.return_value.get_crop_progress.return_value = records
    return patch("cropwatch.cli_volatility.UsdaClient", mock)


def _patch_key(key="testkey"):
    return patch("cropwatch.cli_volatility.get_api_key", return_value=key)


def test_show_volatility_success(runner):
    with _patch_key(), _patch_client():
        result = runner.invoke(volatility_group, ["show", "--commodity", "CORN"])
    assert result.exit_code == 0
    assert "Volatility" in result.output
    assert "Std-dev" in result.output


def test_show_volatility_no_api_key(runner):
    with _patch_key(None):
        result = runner.invoke(volatility_group, ["show"])
    assert result.exit_code != 0
    assert "no API key" in result.output


def test_show_volatility_api_error(runner):
    from cropwatch.usda_client import UsdaClientError
    mock = MagicMock()
    mock.return_value.get_crop_progress.side_effect = UsdaClientError("timeout")
    with _patch_key(), patch("cropwatch.cli_volatility.UsdaClient", mock):
        result = runner.invoke(volatility_group, ["show"])
    assert result.exit_code != 0
    assert "API error" in result.output


def test_show_volatility_too_few_records(runner):
    with _patch_key(), _patch_client([_rec(5.0)]):
        result = runner.invoke(volatility_group, ["show"])
    assert result.exit_code != 0
    assert "Volatility error" in result.output


def test_show_volatility_state_option(runner):
    state_records = [
        {**_rec(10.0, "2023-04-01"), "state_alpha": "IA"},
        {**_rec(22.0, "2023-04-08"), "state_alpha": "IA"},
        {**_rec(38.0, "2023-04-15"), "state_alpha": "IA"},
    ]
    with _patch_key(), _patch_client(state_records):
        result = runner.invoke(volatility_group, ["show", "--state", "IA"])
    assert result.exit_code == 0
    assert "IA" in result.output


def test_show_volatility_empty_records(runner):
    """Verify that an empty record list is handled gracefully."""
    with _patch_key(), _patch_client([]):
        result = runner.invoke(volatility_group, ["show"])
    assert result.exit_code != 0
    assert "Volatility error" in result.output
