"""Integration-style tests for skewness CLI output formatting."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from cropwatch.cli_skewness import skewness_group
from cropwatch.skewness import compute_skewness, format_skewness


@pytest.fixture()
def runner():
    return CliRunner()


def _rec(value, state="NE", commodity="SOYBEANS", week="2023-08-20"):
    return {
        "commodity_desc": commodity,
        "state_alpha": state,
        "Value": str(value),
        "week_ending": week,
    }


def test_format_output_matches_library(runner):
    """CLI output should match what format_skewness produces directly."""
    records = [_rec(v) for v in [30, 35, 40, 45, 50, 80]]
    mock_cls = MagicMock()
    mock_cls.return_value.get_crop_progress.return_value = records

    with patch("cropwatch.cli_skewness.UsdaClient", mock_cls), \
         patch("cropwatch.cli_skewness.get_api_key", return_value="k"):
        result = runner.invoke(skewness_group, ["show", "-c", "SOYBEANS", "-s", "NE"])

    expected = format_skewness(
        compute_skewness(records, commodity="SOYBEANS", state="NE")
    )
    assert result.exit_code == 0
    assert expected in result.output


def test_right_skewed_label_in_output(runner):
    """A right-skewed distribution should mention 'right' in the output."""
    records = [_rec(v) for v in [1, 1, 1, 1, 1, 100]]
    mock_cls = MagicMock()
    mock_cls.return_value.get_crop_progress.return_value = records

    with patch("cropwatch.cli_skewness.UsdaClient", mock_cls), \
         patch("cropwatch.cli_skewness.get_api_key", return_value="k"):
        result = runner.invoke(skewness_group, ["show", "-c", "SOYBEANS", "-s", "NE"])

    assert result.exit_code == 0
    assert "right" in result.output.lower()


def test_symmetric_label_in_output(runner):
    """A near-symmetric distribution should mention 'symmetric' in the output."""
    records = [_rec(v) for v in [48, 49, 50, 51, 52, 50]]
    mock_cls = MagicMock()
    mock_cls.return_value.get_crop_progress.return_value = records

    with patch("cropwatch.cli_skewness.UsdaClient", mock_cls), \
         patch("cropwatch.cli_skewness.get_api_key", return_value="k"):
        result = runner.invoke(skewness_group, ["show", "-c", "SOYBEANS", "-s", "NE"])

    assert result.exit_code == 0
    assert "symmetric" in result.output.lower()
