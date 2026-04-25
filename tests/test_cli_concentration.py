"""Tests for cropwatch.cli_concentration."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from cropwatch.cli_concentration import concentration_group


@pytest.fixture()
def runner():
    return CliRunner()


def _rec(state: str, value: float, commodity: str = "CORN", week: str = "2023-06-04") -> dict:
    return {
        "commodity_desc": commodity,
        "week_ending": week,
        "state_alpha": state,
        "Value": str(value),
    }


_ALL_RECORDS = [
    _rec("IA", 40.0),
    _rec("IL", 30.0),
    _rec("NE", 20.0),
    _rec("MN", 10.0),
]


def _patch_client(records=None):
    if records is None:
        records = _ALL_RECORDS
    mock = MagicMock()
    mock.get_crop_progress.return_value = records
    return patch("cropwatch.cli_concentration.UsdaClient", return_value=mock)


def _patch_key(key="testkey"):
    return patch("cropwatch.cli_concentration.get_api_key", return_value=key)


def test_hhi_success(runner):
    with _patch_key(), _patch_client():
        result = runner.invoke(concentration_group, ["hhi", "--week", "2023-06-04"])
    assert result.exit_code == 0
    assert "HHI" in result.output
    assert "IA" in result.output


def test_hhi_no_api_key(runner):
    with patch("cropwatch.cli_concentration.get_api_key", return_value=None):
        result = runner.invoke(concentration_group, ["hhi", "--week", "2023-06-04"])
    assert result.exit_code != 0
    assert "API key" in result.output


def test_hhi_api_error(runner):
    from cropwatch.usda_client import UsdaClientError
    mock = MagicMock()
    mock.get_crop_progress.side_effect = UsdaClientError("timeout")
    with _patch_key(), patch("cropwatch.cli_concentration.UsdaClient", return_value=mock):
        result = runner.invoke(concentration_group, ["hhi", "--week", "2023-06-04"])
    assert result.exit_code != 0
    assert "API error" in result.output


def test_hhi_no_data(runner):
    with _patch_key(), _patch_client(records=[]):
        result = runner.invoke(concentration_group, ["hhi", "--week", "2023-06-04"])
    assert result.exit_code != 0
    assert "error" in result.output.lower()


def test_hhi_custom_commodity(runner):
    soy_records = [_rec(s, v, "SOYBEANS") for s, v in [("IA", 50.0), ("IL", 50.0)]]
    with _patch_key(), _patch_client(records=soy_records):
        result = runner.invoke(
            concentration_group,
            ["hhi", "--commodity", "SOYBEANS", "--week", "2023-06-04"],
        )
    assert result.exit_code == 0
    assert "SOYBEANS" in result.output
