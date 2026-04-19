from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import pytest
from cropwatch.cli_heatmap import heatmap_group


@pytest.fixture()
def runner():
    return CliRunner()


RECORDS = [
    {"commodity_desc": "CORN", "week_ending": "2024-05-05", "state_alpha": "IA", "Value": "72"},
    {"commodity_desc": "CORN", "week_ending": "2024-05-05", "state_alpha": "IL", "Value": "55"},
]


def _patch_client(records=None):
    m = MagicMock()
    m.return_value.get_crop_progress.return_value = records or RECORDS
    return patch("cropwatch.cli_heatmap.UsdaClient", m)


def test_show_heatmap_success(runner):
    with _patch_client(), patch("cropwatch.cli_heatmap.get_api_key", return_value="k"):
        result = runner.invoke(heatmap_group, ["show", "--week", "2024-05-05"])
    assert result.exit_code == 0
    assert "IA" in result.output
    assert "IL" in result.output


def test_show_heatmap_no_api_key(runner):
    with patch("cropwatch.cli_heatmap.get_api_key", return_value=None):
        result = runner.invoke(heatmap_group, ["show", "--week", "2024-05-05"])
    assert result.exit_code != 0
    assert "API key" in result.output


def test_show_heatmap_api_error(runner):
    from cropwatch.usda_client import UsdaClientError
    m = MagicMock()
    m.return_value.get_crop_progress.side_effect = UsdaClientError("fail")
    with patch("cropwatch.cli_heatmap.UsdaClient", m), \
         patch("cropwatch.cli_heatmap.get_api_key", return_value="k"):
        result = runner.invoke(heatmap_group, ["show", "--week", "2024-05-05"])
    assert result.exit_code != 0
    assert "API error" in result.output


def test_show_heatmap_no_data(runner):
    with _patch_client([]), patch("cropwatch.cli_heatmap.get_api_key", return_value="k"):
        result = runner.invoke(heatmap_group, ["show", "--week", "2024-05-05"])
    assert result.exit_code != 0
    assert "Heatmap error" in result.output


def test_show_heatmap_contains_range(runner):
    with _patch_client(), patch("cropwatch.cli_heatmap.get_api_key", return_value="k"):
        result = runner.invoke(heatmap_group, ["show", "--week", "2024-05-05"])
    assert "Range:" in result.output
