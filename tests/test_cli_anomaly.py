from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from cropwatch.cli_anomaly import anomaly_group


@pytest.fixture
def runner():
    return CliRunner()


def _patch_client(records):
    mock = MagicMock()
    mock.return_value.get_crop_progress.return_value = records
    return patch("cropwatch.cli_anomaly.UsdaClient", mock)


def _patch_key(key="testkey"):
    return patch("cropwatch.cli_anomaly.get_api_key", return_value=key)


def test_scan_no_anomalies(runner):
    records = [{"week_ending": f"2023-0{i+1}-01", "value": 50} for i in range(5)]
    with _patch_key(), _patch_client(records):
        result = runner.invoke(anomaly_group, ["scan", "--crop", "corn", "--year", "2023"])
    assert result.exit_code == 0
    assert "No anomalies" in result.output


def test_scan_finds_anomaly(runner):
    records = [{"week_ending": f"2023-0{i+1}-01", "value": 50 if i < 4 else 95} for i in range(5)]
    with _patch_key(), _patch_client(records):
        result = runner.invoke(anomaly_group, ["scan", "--crop", "corn", "--year", "2023"])
    assert result.exit_code == 0
    assert "95" in result.output


def test_scan_no_api_key(runner):
    with patch("cropwatch.cli_anomaly.get_api_key", return_value=None):
        result = runner.invoke(anomaly_group, ["scan"])
    assert result.exit_code != 0
    assert "API key" in result.output


def test_scan_api_error(runner):
    from cropwatch.usda_client import UsdaClientError
    mock = MagicMock()
    mock.return_value.get_crop_progress.side_effect = UsdaClientError("fail")
    with _patch_key(), patch("cropwatch.cli_anomaly.UsdaClient", mock):
        result = runner.invoke(anomaly_group, ["scan"])
    assert result.exit_code != 0
    assert "API error" in result.output


def test_scan_no_data(runner):
    with _patch_key(), _patch_client([]):
        result = runner.invoke(anomaly_group, ["scan"])
    assert result.exit_code == 0
    assert "No data" in result.output


def test_scan_with_state(runner):
    records = [{"week_ending": f"2023-0{i+1}-01", "value": 50} for i in range(5)]
    with _patch_key(), _patch_client(records):
        result = runner.invoke(anomaly_group, ["scan", "--state", "IA"])
    assert result.exit_code == 0
    assert "IA" in result.output
