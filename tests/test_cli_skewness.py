"""Tests for cropwatch.cli_skewness."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from cropwatch.cli_skewness import skewness_group


@pytest.fixture()
def runner():
    return CliRunner()


def _rec(value, state="IA", commodity="CORN", week="2023-06-04"):
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "Value": str(value),
        "week_ending": week,
    }


def _patch_client(records):
    mock = MagicMock()
    mock.return_value.get_crop_progress.return_value = records
    return patch("cropwatch.cli_skewness.UsdaClient", mock)


def _patch_key(key="test-key"):
    return patch("cropwatch.cli_skewness.get_api_key", return_value=key)


def test_show_skewness_success(runner):
    records = [_rec(v) for v in [40, 45, 50, 55, 60, 65]]
    with _patch_key(), _patch_client(records):
        result = runner.invoke(skewness_group, ["show", "-c", "CORN", "-s", "IA"])
    assert result.exit_code == 0
    assert "CORN" in result.output
    assert "Skewness" in result.output


def test_show_skewness_no_api_key(runner):
    with _patch_key(None):
        result = runner.invoke(skewness_group, ["show", "-c", "CORN"])
    assert result.exit_code != 0
    assert "API key" in result.output


def test_show_skewness_api_error(runner):
    from cropwatch.usda_client import UsdaClientError
    mock = MagicMock()
    mock.return_value.get_crop_progress.side_effect = UsdaClientError("network fail")
    with _patch_key(), patch("cropwatch.cli_skewness.UsdaClient", mock):
        result = runner.invoke(skewness_group, ["show", "-c", "CORN"])
    assert result.exit_code != 0
    assert "network fail" in result.output


def test_show_skewness_too_few_records(runner):
    records = [_rec(50), _rec(60)]  # only 2 records
    with _patch_key(), _patch_client(records):
        result = runner.invoke(skewness_group, ["show", "-c", "CORN", "-s", "IA"])
    assert result.exit_code != 0
    assert "Not enough" in result.output or "Error" in result.output


def test_show_skewness_with_year(runner):
    records = [_rec(v) for v in [38, 42, 50, 58, 62, 66]]
    with _patch_key(), _patch_client(records) as mock_cls:
        result = runner.invoke(
            skewness_group, ["show", "-c", "CORN", "-s", "IA", "-y", "2022"]
        )
        mock_cls.return_value.get_crop_progress.assert_called_once_with(
            commodity_desc="CORN", state_alpha="IA", year=2022
        )
    assert result.exit_code == 0
