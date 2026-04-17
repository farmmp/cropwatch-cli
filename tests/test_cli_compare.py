import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from cropwatch.cli_compare import compare_group

CURRENT = [{"week_ending": "2024-05-05", "commodity_desc": "CORN", "Value": "62"}]
PREVIOUS = [{"week_ending": "2024-05-05", "commodity_desc": "CORN", "Value": "55"}]


@pytest.fixture
def runner():
    return CliRunner()


def _patch_client(cur, prev):
    mock_client = MagicMock()
    mock_client.get_crop_progress.side_effect = [cur, prev]
    return patch("cropwatch.cli_compare.UsdaClient", return_value=mock_client)


def test_yoy_success(runner):
    with patch("cropwatch.cli_compare.get_api_key", return_value="key"):
        with _patch_client(CURRENT, PREVIOUS):
            result = runner.invoke(compare_group, ["yoy", "CORN", "2024-05-05"])
    assert result.exit_code == 0
    assert "CORN" in result.output
    assert "62" in result.output
    assert "55" in result.output


def test_yoy_no_api_key(runner):
    with patch("cropwatch.cli_compare.get_api_key", return_value=None):
        result = runner.invoke(compare_group, ["yoy", "CORN", "2024-05-05"])
    assert result.exit_code != 0
    assert "API key" in result.output


def test_yoy_bad_week_format(runner):
    with patch("cropwatch.cli_compare.get_api_key", return_value="key"):
        result = runner.invoke(compare_group, ["yoy", "CORN", "bad-date"])
    assert result.exit_code != 0
    assert "YYYY-MM-DD" in result.output


def test_yoy_api_error(runner):
    from cropwatch.usda_client import UsdaClientError
    mock_client = MagicMock()
    mock_client.get_crop_progress.side_effect = UsdaClientError("timeout")
    with patch("cropwatch.cli_compare.get_api_key", return_value="key"):
        with patch("cropwatch.cli_compare.UsdaClient", return_value=mock_client):
            result = runner.invoke(compare_group, ["yoy", "CORN", "2024-05-05"])
    assert result.exit_code != 0
    assert "timeout" in result.output


def test_yoy_no_data_raises(runner):
    with patch("cropwatch.cli_compare.get_api_key", return_value="key"):
        with _patch_client([], []):
            result = runner.invoke(compare_group, ["yoy", "CORN", "2024-05-05"])
    assert result.exit_code != 0
