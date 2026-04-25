"""CLI tests for the regime scan command."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from cropwatch.cli_regime import regime_group
from cropwatch.regime import RegimeError
from cropwatch.usda_client import UsdaClientError


@pytest.fixture()
def runner():
    return CliRunner()


def _rec(week: str, value: float) -> dict:
    return {
        "commodity_desc": "CORN",
        "week_ending": week,
        "Value": str(value),
        "state_alpha": "US",
    }


_RECORDS = [
    _rec("2023-05-01", 10.0),
    _rec("2023-05-08", 20.0),
    _rec("2023-05-15", 30.0),
    _rec("2023-05-22", 40.0),
    _rec("2023-05-29", 50.0),
]


def _patch_client(records=None):
    if records is None:
        records = _RECORDS
    return patch(
        "cropwatch.cli_regime.UsdaClient.get_crop_progress",
        return_value=records,
    )


def _patch_key(key="test-key"):
    return patch("cropwatch.cli_regime.get_api_key", return_value=key)


def test_scan_success(runner):
    with _patch_key(), _patch_client():
        result = runner.invoke(regime_group, ["scan", "--commodity", "CORN"])
    assert result.exit_code == 0
    assert "Regime" in result.output


def test_scan_no_api_key(runner):
    with _patch_key(key=None):
        result = runner.invoke(regime_group, ["scan", "--commodity", "CORN"])
    assert result.exit_code != 0
    assert "API key" in result.output


def test_scan_api_error(runner):
    with _patch_key(), patch(
        "cropwatch.cli_regime.UsdaClient.get_crop_progress",
        side_effect=UsdaClientError("timeout"),
    ):
        result = runner.invoke(regime_group, ["scan", "--commodity", "CORN"])
    assert result.exit_code != 0
    assert "API error" in result.output


def test_scan_regime_error(runner):
    with _patch_key(), _patch_client(records=[]):
        result = runner.invoke(regime_group, ["scan", "--commodity", "CORN"])
    assert result.exit_code != 0
    assert "Regime error" in result.output


def test_scan_shifts_only_flag(runner):
    with _patch_key(), _patch_client():
        result = runner.invoke(
            regime_group, ["scan", "--commodity", "CORN", "--shifts-only"]
        )
    assert result.exit_code == 0
    # Either shifts are printed or the 'No regime shifts' message appears
    assert "SHIFT" in result.output or "No regime shifts" in result.output


def test_scan_with_threshold(runner):
    with _patch_key(), _patch_client():
        result = runner.invoke(
            regime_group,
            ["scan", "--commodity", "CORN", "--threshold", "100"],
        )
    assert result.exit_code == 0
    assert "neutral" in result.output
