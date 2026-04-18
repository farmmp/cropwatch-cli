"""Tests for cropwatch.cli_forecast."""
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from cropwatch.cli_forecast import forecast_group
from cropwatch.usda_client import UsdaClientError


@pytest.fixture()
def runner():
    return CliRunner()


def _patch_client(records):
    mock = MagicMock()
    mock.return_value.get_crop_progress.return_value = records
    return patch("cropwatch.cli_forecast.UsdaClient", mock)


SAMPLE_RECORDS = [
    {"commodity_desc": "Corn", "Value": str(v), "week_ending": f"2024-0{i+1}-01"}
    for i, v in enumerate([10, 20, 30, 40, 50])
]


def test_predict_success(runner):
    with _patch_client(SAMPLE_RECORDS):
        result = runner.invoke(
            forecast_group, ["predict", "--commodity", "Corn", "--api-key", "testkey"]
        )
    assert result.exit_code == 0
    assert "Forecast" in result.output
    assert "%" in result.output


def test_predict_no_api_key(runner):
    with patch("cropwatch.cli_forecast.get_api_key", return_value=None):
        result = runner.invoke(forecast_group, ["predict"])
    assert result.exit_code != 0
    assert "API key" in result.output


def test_predict_api_error(runner):
    with patch("cropwatch.cli_forecast.UsdaClient") as mock_cls:
        mock_cls.return_value.get_crop_progress.side_effect = UsdaClientError("timeout")
        result = runner.invoke(forecast_group, ["predict", "--api-key", "k"])
    assert result.exit_code != 0
    assert "API error" in result.output


def test_predict_no_data(runner):
    with _patch_client([]):
        result = runner.invoke(
            forecast_group, ["predict", "--api-key", "k", "--commodity", "Corn"]
        )
    assert result.exit_code == 0
    assert "No data" in result.output


def test_predict_weeks_ahead(runner):
    with _patch_client(SAMPLE_RECORDS):
        result = runner.invoke(
            forecast_group,
            ["predict", "--commodity", "Corn", "--weeks-ahead", "3", "--api-key", "testkey"],
        )
    assert result.exit_code == 0
    assert "+3" in result.output
