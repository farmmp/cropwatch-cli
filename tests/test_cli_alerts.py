"""Tests for the alerts CLI sub-commands."""

import json
from pathlib import Path
from click.testing import CliRunner
import pytest

from cropwatch.cli_alerts import alerts_group
from cropwatch import alerts as alerts_module


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def patch_alerts_path(tmp_path, monkeypatch):
    """Redirect all alert I/O to a temp file."""
    tmp_file = tmp_path / "alerts.json"
    monkeypatch.setattr(alerts_module, "DEFAULT_ALERTS_FILE", tmp_file)
    return tmp_file


def test_add_alert_success(runner):
    result = runner.invoke(alerts_group, ["add", "CORN", "PROGRESS", "50"])
    assert result.exit_code == 0
    assert "Alert added" in result.output
    assert "CORN" in result.output


def test_add_alert_above(runner):
    result = runner.invoke(
        alerts_group, ["add", "SOYBEANS", "HARVESTED", "75", "--condition", "above"]
    )
    assert result.exit_code == 0
    assert "above" in result.output


def test_add_alert_invalid_condition(runner):
    result = runner.invoke(
        alerts_group, ["add", "CORN", "PROGRESS", "50", "--condition", "equal"]
    )
    assert result.exit_code != 0


def test_list_alerts_empty(runner):
    result = runner.invoke(alerts_group, ["list"])
    assert result.exit_code == 0
    assert "No alerts" in result.output


def test_list_alerts_shows_rules(runner):
    runner.invoke(alerts_group, ["add", "CORN", "PROGRESS", "40"])
    runner.invoke(alerts_group, ["add", "WHEAT", "PLANTED", "60", "--condition", "above"])
    result = runner.invoke(alerts_group, ["list"])
    assert result.exit_code == 0
    assert "CORN" in result.output
    assert "WHEAT" in result.output


def test_clear_alerts(runner):
    runner.invoke(alerts_group, ["add", "CORN", "PROGRESS", "40"])
    result = runner.invoke(alerts_group, ["clear"], input="y\n")
    assert result.exit_code == 0
    assert "cleared" in result.output
    list_result = runner.invoke(alerts_group, ["list"])
    assert "No alerts" in list_result.output
