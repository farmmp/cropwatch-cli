"""Integration tests for the inflection CLI command."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from cropwatch.cli_inflection import inflection_group
from cropwatch.inflection import InflectionError
from cropwatch.usda_client import UsdaClientError


@pytest.fixture()
def runner():
    return CliRunner()


def _rec(week: str, value: float) -> dict:
    return {
        "week_ending": week,
        "Value": str(value),
        "commodity_desc": "CORN",
        "state_alpha": "US",
    }


_RECORDS = [
    _rec("2023-05-07", 10.0),
    _rec("2023-05-14", 60.0),
    _rec("2023-05-21", 20.0),
]


def _patch_client(records=None):
    if records is None:
        records = _RECORDS
    return patch(
        "cropwatch.cli_inflection.UsdaClient.get_crop_progress",
        return_value=records,
    )


def _patch_key(key="test-key"):
    return patch("cropwatch.cli_inflection.get_api_key", return_value=key)


def test_scan_success(runner):
    with _patch_key(), _patch_client():
        result = runner.invoke(inflection_group, ["scan", "--commodity", "CORN", "--year", "2023"])
    assert result.exit_code == 0
    assert "CORN" in result.output


def test_scan_no_api_key(runner):
    with _patch_key(key=None):
        result = runner.invoke(inflection_group, ["scan"])
    assert result.exit_code != 0
    assert "API key" in result.output


def test_scan_api_error(runner):
    with _patch_key(), patch(
        "cropwatch.cli_inflection.UsdaClient.get_crop_progress",
        side_effect=UsdaClientError("timeout"),
    ):
        result = runner.invoke(inflection_group, ["scan"])
    assert result.exit_code != 0
    assert "API error" in result.output


def test_scan_inflection_error(runner):
    with _patch_key(), patch(
        "cropwatch.cli_inflection.UsdaClient.get_crop_progress",
        return_value=[_rec("2023-05-07", 10.0)],  # too few
    ):
        result = runner.invoke(inflection_group, ["scan"])
    assert result.exit_code != 0
    assert "Inflection error" in result.output


def test_scan_no_inflections_message(runner):
    flat = [
        _rec("2023-05-07", 10.0),
        _rec("2023-05-14", 20.0),
        _rec("2023-05-21", 30.0),
    ]
    with _patch_key(), _patch_client(records=flat):
        result = runner.invoke(inflection_group, ["scan", "--min-change", "50"])
    assert result.exit_code == 0
    assert "No inflection" in result.output
