"""Tests for cropwatch.cli_trend."""
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from cropwatch.cli_trend import trend_group


@pytest.fixture
def runner():
    return CliRunner()


SAMPLE_DATA = [
    {"Week_Ending": "2024-04-07", "Value": "28"},
    {"Week_Ending": "2024-04-14", "Value": "52"},
    {"Week_Ending": "2024-04-21", "Value": "74"},
]


def _patch_client(data=SAMPLE_DATA, raises=None):
    mock = MagicMock()
    if raises:
        mock.return_value.get_crop_progress.side_effect = raises
    else:
        mock.return_value.get_crop_progress.return_value = data
    return patch("cropwatch.cli_trend.UsdaClient", mock)


def test_show_trend_success(runner):
    with _patch_client(), patch("cropwatch.cli_trend.get_api_key", return_value="key123"):
        result = runner.invoke(trend_group, ["show", "--crop", "CORN"])
    assert result.exit_code == 0
    assert "Trend:" in result.output
    assert "2024-04-07" in result.output


def test_show_trend_no_api_key(runner):
    with patch("cropwatch.cli_trend.get_api_key", return_value=None):
        result = runner.invoke(trend_group, ["show"])
    assert result.exit_code != 0
    assert "API key" in result.output


def test_show_trend_api_error(runner):
    from cropwatch.usda_client import UsdaClientError
    with _patch_client(raises=UsdaClientError("timeout")), \
         patch("cropwatch.cli_trend.get_api_key", return_value="k"):
        result = runner.invoke(trend_group, ["show"])
    assert result.exit_code != 0
    assert "API error" in result.output


def test_show_trend_no_data(runner):
    with _patch_client(data=[]), patch("cropwatch.cli_trend.get_api_key", return_value="k"):
        result = runner.invoke(trend_group, ["show"])
    assert result.exit_code == 0
    assert "No data" in result.output


def test_show_trend_with_state(runner):
    with _patch_client(), patch("cropwatch.cli_trend.get_api_key", return_value="k"):
        result = runner.invoke(trend_group, ["show", "--state", "IA"])
    assert result.exit_code == 0
    assert "Trend:" in result.output
