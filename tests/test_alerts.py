"""Tests for cropwatch.alerts module."""

import pytest
from pathlib import Path
from cropwatch.alerts import (
    load_alerts, save_alert, check_alerts, clear_alerts, AlertError
)


@pytest.fixture
def alert_path(tmp_path: Path) -> Path:
    return tmp_path / "alerts.json"


def test_load_alerts_empty(alert_path):
    assert load_alerts(alert_path) == []


def test_save_and_load_alert(alert_path):
    rule = save_alert("CORN", "PROGRESS", 50.0, "below", path=alert_path)
    assert rule["commodity"] == "CORN"
    assert rule["threshold"] == 50.0
    loaded = load_alerts(alert_path)
    assert len(loaded) == 1
    assert loaded[0]["condition"] == "below"


def test_multiple_alerts_accumulate(alert_path):
    save_alert("CORN", "PROGRESS", 40.0, "below", path=alert_path)
    save_alert("SOYBEANS", "HARVESTED", 80.0, "above", path=alert_path)
    assert len(load_alerts(alert_path)) == 2


def test_invalid_condition_raises(alert_path):
    with pytest.raises(AlertError, match="Invalid condition"):
        save_alert("CORN", "PROGRESS", 50.0, condition="equal", path=alert_path)


def test_check_alerts_triggered(alert_path):
    save_alert("CORN", "PROGRESS", 50.0, "below", path=alert_path)
    data = [
        {"commodity_desc": "CORN", "short_desc": "CORN - PROGRESS", "Value": "35"},
    ]
    results = check_alerts(data, path=alert_path)
    assert len(results) == 1
    assert results[0]["value"] == 35.0


def test_check_alerts_not_triggered(alert_path):
    save_alert("CORN", "PROGRESS", 50.0, "below", path=alert_path)
    data = [
        {"commodity_desc": "CORN", "short_desc": "CORN - PROGRESS", "Value": "65"},
    ]
    results = check_alerts(data, path=alert_path)
    assert results == []


def test_check_alerts_above_condition(alert_path):
    save_alert("SOYBEANS", "HARVESTED", 70.0, "above", path=alert_path)
    data = [
        {"commodity_desc": "SOYBEANS", "short_desc": "SOYBEANS - HARVESTED", "Value": "85"},
    ]
    results = check_alerts(data, path=alert_path)
    assert len(results) == 1


def test_check_alerts_commodity_mismatch(alert_path):
    save_alert("CORN", "PROGRESS", 50.0, "below", path=alert_path)
    data = [
        {"commodity_desc": "WHEAT", "short_desc": "WHEAT - PROGRESS", "Value": "20"},
    ]
    assert check_alerts(data, path=alert_path) == []


def test_clear_alerts(alert_path):
    save_alert("CORN", "PROGRESS", 50.0, path=alert_path)
    clear_alerts(alert_path)
    assert load_alerts(alert_path) == []


def test_clear_alerts_no_file(alert_path):
    # Should not raise even if file does not exist
    clear_alerts(alert_path)
