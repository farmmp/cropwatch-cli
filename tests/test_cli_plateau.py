"""CLI tests for the plateau scan command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cropwatch.cli_plateau import plateau_group
from cropwatch.plateau import PlateauError
from cropwatch.usda_client import UsdaClientError


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _rec(week: str, value: float) -> dict:
    return {
        "commodity_desc": "CORN",
        "state_alpha": "IA",
        "week_ending": week,
        "Value": str(value),
    }


def _patch_client(records):
    mock = MagicMock()
    mock.return_value.get_crop_progress.return_value = records
    return patch("cropwatch.cli_plateau.UsdaClient", mock)


def _patch_key(key: str = "testkey"):
    return patch("cropwatch.cli_plateau.get_api_key", return_value=key)


def _flat_records():
    return [
        _rec("2023-04-09", 50.0),
        _rec("2023-04-16", 50.3),
        _rec("2023-04-23", 50.1),
        _rec("2023-04-30", 50.6),
    ]


def test_scan_success(runner):
    with _patch_key(), _patch_client(_flat_records()):
        result = runner.invoke(
            plateau_group, ["scan", "--commodity", "CORN", "--state", "IA"]
        )
    assert result.exit_code == 0
    assert "CORN" in result.output


def test_scan_no_api_key(runner):
    with _patch_key(key=None):
        result = runner.invoke(
            plateau_group, ["scan", "--commodity", "CORN"]
        )
    assert result.exit_code != 0
    assert "API key" in result.output


def test_scan_api_error(runner):
    with _patch_key(), _patch_client(None) as mock_cls:
        mock_cls.return_value.get_crop_progress.side_effect = UsdaClientError("boom")
        result = runner.invoke(
            plateau_group, ["scan", "--commodity", "CORN"]
        )
    assert result.exit_code != 0
    assert "boom" in result.output


def test_scan_plateau_error(runner):
    with _patch_key(), _patch_client([]) as mock_cls:
        mock_cls.return_value.get_crop_progress.return_value = []
        with patch(
            "cropwatch.cli_plateau.detect_plateaus",
            side_effect=PlateauError("no data"),
        ):
            result = runner.invoke(
                plateau_group, ["scan", "--commodity", "CORN"]
            )
    assert result.exit_code != 0
    assert "no data" in result.output


def test_scan_no_plateaus_message(runner):
    """When no plateaus are found, output should say so gracefully."""
    records = [
        _rec("2023-04-09", 10.0),
        _rec("2023-04-16", 30.0),
        _rec("2023-04-23", 60.0),
        _rec("2023-04-30", 90.0),
    ]
    with _patch_key(), _patch_client(records):
        result = runner.invoke(
            plateau_group,
            ["scan", "--commodity", "CORN", "--min-weeks", "3"],
        )
    assert result.exit_code == 0
    assert "No plateaus" in result.output
