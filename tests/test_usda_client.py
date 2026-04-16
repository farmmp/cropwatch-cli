"""Unit tests for cropwatch.usda_client."""

import pytest
import responses  # pip install responses
from responses import matchers

from cropwatch.usda_client import UsdaClient, UsdaClientError, NASS_API_BASE

API_KEY = "test-api-key-123"


@pytest.fixture()
def client():
    return UsdaClient(api_key=API_KEY)


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("USDA_NASS_API_KEY", raising=False)
    with pytest.raises(UsdaClientError, match="No API key"):
        UsdaClient()


def test_env_var_api_key(monkeypatch):
    monkeypatch.setenv("USDA_NASS_API_KEY", "env-key")
    c = UsdaClient()
    assert c.api_key == "env-key"


@responses.activate
def test_get_crop_progress_success(client):
    sample_data = [
        {"commodity_desc": "CORN", "week_ending": "2023-05-07", "Value": "12"},
        {"commodity_desc": "CORN", "week_ending": "2023-05-14", "Value": "28"},
    ]
    responses.get(
        f"{NASS_API_BASE}/api_GET/",
        json={"data": sample_data},
        status=200,
    )

    result = client.get_crop_progress("CORN", 2023)
    assert len(result) == 2
    assert result[0]["Value"] == "12"


@responses.activate
def test_get_crop_progress_with_state(client):
    responses.get(
        f"{NASS_API_BASE}/api_GET/",
        json={"data": [{"state_alpha": "IA", "Value": "45"}]},
        status=200,
    )

    result = client.get_crop_progress("SOYBEANS", 2023, state_alpha="ia")
    assert result[0]["state_alpha"] == "IA"


@responses.activate
def test_get_crop_progress_http_error(client):
    responses.get(f"{NASS_API_BASE}/api_GET/", status=403)
    with pytest.raises(UsdaClientError, match="Request failed"):
        client.get_crop_progress("CORN", 2023)


@responses.activate
def test_get_crop_progress_bad_payload(client):
    responses.get(f"{NASS_API_BASE}/api_GET/", json={"error": "bad request"}, status=200)
    with pytest.raises(UsdaClientError, match="Unexpected API response"):
        client.get_crop_progress("CORN", 2023)
