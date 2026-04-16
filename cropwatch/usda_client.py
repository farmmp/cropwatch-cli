"""Client for fetching USDA NASS crop progress data via the Quick Stats API."""

import os
import requests
from typing import Optional

NASS_API_BASE = "https://quickstats.nass.usda.gov/api"
API_KEY_ENV = "USDA_NASS_API_KEY"


class UsdaClientError(Exception):
    """Raised when the USDA API returns an error or is unreachable."""


class UsdaClient:
    """Thin wrapper around the USDA NASS Quick Stats REST API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get(API_KEY_ENV)
        if not self.api_key:
            raise UsdaClientError(
                f"No API key provided. Set the {API_KEY_ENV} environment variable "
                "or pass api_key= explicitly."
            )
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get_crop_progress(
        self,
        commodity: str,
        year: int,
        state_alpha: Optional[str] = None,
    ) -> list[dict]:
        """Return crop progress/condition records for *commodity* and *year*.

        Parameters
        ----------
        commodity:
            Crop name as used by NASS, e.g. ``"CORN"`` or ``"SOYBEANS"``.
        year:
            Marketing / survey year (e.g. 2023).
        state_alpha:
            Optional two-letter state abbreviation (e.g. ``"IA"``).
            When omitted the national-level data is returned.
        """
        params: dict = {
            "key": self.api_key,
            "source_desc": "SURVEY",
            "sector_desc": "CROPS",
            "group_desc": "FIELD CROPS",
            "commodity_desc": commodity.upper(),
            "statisticcat_desc": "PROGRESS",
            "freq_desc": "WEEKLY",
            "year": year,
            "format": "JSON",
        }
        if state_alpha:
            params["state_alpha"] = state_alpha.upper()
        else:
            params["agg_level_desc"] = "NATIONAL"

        try:
            response = self.session.get(f"{NASS_API_BASE}/api_GET/", params=params, timeout=15)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise UsdaClientError(f"Request failed: {exc}") from exc

        payload = response.json()
        if "data" not in payload:
            raise UsdaClientError(f"Unexpected API response: {payload}")

        return payload["data"]
