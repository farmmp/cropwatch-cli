import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from cropwatch.cli import cli
from cropwatch.usda_client import UsdaClientError

SAMPLE_DATA = [
    {"commodity_desc": "CORN", "state_alpha": "US", "week_ending": "2023-05-07",
     "short_desc": "CORN - PROGRESS, MEASURED IN PCT PLANTED", "Value": "35"},
    {"commodity_desc": "CORN", "state_alpha": "US", "week_ending": "2023-05-14",
     "short_desc": "CORN - PROGRESS, MEASURED IN PCT PLANTED", "Value": "65"},
]


@pytest.fixture
def runner():
    return CliRunner()


@patch("cropwatch.cli.UsdaClient")
def test_progress_default(mock_client_cls, runner):
    mock_client = MagicMock()
    mock_client.get_crop_progress.return_value = SAMPLE_DATA
    mock_client_cls.return_value = mock_client

    result = runner.invoke(cli, ["progress", "CORN", "--api-key", "testkey"])
    assert result.exit_code == 0
    assert "CORN" in result.output


@patch("cropwatch.cli.UsdaClient")
def test_progress_simple_flag(mock_client_cls, runner):
    mock_client = MagicMock()
    mock_client.get_crop_progress.return_value = SAMPLE_DATA
    mock_client_cls.return_value = mock_client

    result = runner.invoke(cli, ["progress", "CORN", "--simple", "--api-key", "testkey"])
    assert result.exit_code == 0
    assert "2023-05-07" in result.output


@patch("cropwatch.cli.UsdaClient")
def test_progress_no_data(mock_client_cls, runner):
    mock_client = MagicMock()
    mock_client.get_crop_progress.return_value = []
    mock_client_cls.return_value = mock_client

    result = runner.invoke(cli, ["progress", "CORN", "--api-key", "testkey"])
    assert result.exit_code == 0
    assert "No data found" in result.output


@patch("cropwatch.cli.UsdaClient")
def test_progress_api_error(mock_client_cls, runner):
    mock_client_cls.side_effect = UsdaClientError("Invalid API key")

    result = runner.invoke(cli, ["progress", "CORN", "--api-key", "bad"])
    assert result.exit_code != 0
    assert "Invalid API key" in result.output


@patch("cropwatch.cli.UsdaClient")
def test_ping_success(mock_client_cls, runner):
    mock_client = MagicMock()
    mock_client.get_crop_progress.return_value = SAMPLE_DATA
    mock_client_cls.return_value = mock_client

    result = runner.invoke(cli, ["ping", "--api-key", "testkey"])
    assert result.exit_code == 0
    assert "successful" in result.output
