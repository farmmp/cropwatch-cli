"""Lightweight integration-style tests: transition module + CLI wired together."""
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from cropwatch.cli_transition import transition_group
from cropwatch.transition import detect_transitions, format_transitions, TransitionResult


@pytest.fixture()
def runner():
    return CliRunner()


def _rec(week, val, commodity="CORN", state="US"):
    return {"week_ending": week, "Value": str(val), "commodity_desc": commodity, "state_alpha": state}


_FLAT = [
    _rec("2023-05-01", 50.0),
    _rec("2023-05-08", 50.0),
    _rec("2023-05-15", 50.0),
]


def test_all_flat_dominant_direction():
    result = detect_transitions(_FLAT, "CORN", "US")
    assert result.dominant_direction == "flat"
    assert result.avg_magnitude == pytest.approx(0.0)


def test_format_includes_arrows():
    result = detect_transitions(
        [_rec("2023-04-01", 10), _rec("2023-04-08", 20)], "CORN", "US"
    )
    out = format_transitions(result)
    assert "▲" in out


def test_cli_output_matches_format(runner):
    records = [
        _rec("2023-04-01", 10),
        _rec("2023-04-08", 20),
        _rec("2023-04-15", 15),
    ]
    mock = MagicMock()
    mock.return_value.get_crop_progress.return_value = records
    with patch("cropwatch.cli_transition.get_api_key", return_value="key"), \
         patch("cropwatch.cli_transition.UsdaClient", mock):
        result = runner.invoke(transition_group, ["scan", "--commodity", "CORN"])

    # Verify CLI output matches what format_transitions would produce directly
    direct = format_transitions(detect_transitions(records, "CORN", "US"))
    assert result.exit_code == 0
    for line in direct.splitlines():
        assert line in result.output


def test_cli_dominant_direction_visible(runner):
    records = [
        _rec("2023-04-01", 5),
        _rec("2023-04-08", 10),
        _rec("2023-04-15", 20),
    ]
    mock = MagicMock()
    mock.return_value.get_crop_progress.return_value = records
    with patch("cropwatch.cli_transition.get_api_key", return_value="key"), \
         patch("cropwatch.cli_transition.UsdaClient", mock):
        result = runner.invoke(transition_group, ["scan", "--commodity", "CORN"])
    assert "up" in result.output
