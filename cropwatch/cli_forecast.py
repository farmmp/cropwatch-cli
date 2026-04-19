"""CLI commands for crop progress forecasting."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.forecast import ForecastError, extract_series, forecast, format_forecast


@click.group("forecast")
def forecast_group():
    """Forecast future crop progress using linear trend extrapolation."""


@forecast_group.command("predict")
@click.option("--commodity", "-c", default="Corn", show_default=True, help="Commodity name.")
@click.option("--year", "-y", default=2024, show_default=True, type=int, help="Crop year.")
@click.option("--state", "-s", default=None, help="State abbreviation (optional).")
@click.option("--weeks-ahead", "-w", default=1, show_default=True, type=int,
              help="Weeks ahead to forecast.")
@click.option("--api-key", envvar="USDA_API_KEY", default=None, hidden=True)
def predict(commodity: str, year: int, state: str | None, weeks_ahead: int, api_key: str | None):
    """Predict crop progress N weeks ahead based on historical season data."""
    if weeks_ahead < 1:
        click.echo("Error: --weeks-ahead must be at least 1.", err=True)
        raise SystemExit(1)

    key = api_key or get_api_key()
    if not key:
        click.echo("Error: No API key configured. Set USDA_API_KEY or run `cropwatch config set-key`.", err=True)
        raise SystemExit(1)

    try:
        client = UsdaClient(api_key=key)
        params = {"year": year, "commodity_desc": commodity}
        if state:
            params["state_alpha"] = state.upper()
        records = client.get_crop_progress(**params)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)

    if not records:
        click.echo("No data returned for the given parameters.")
        return

    try:
        series = extract_series(records, commodity)
        if not series:
            click.echo(f"No numeric values found for '{commodity}'.")
            return
        result = forecast(series, weeks_ahead=weeks_ahead)
        click.echo(format_forecast(result, commodity))
    except ForecastError as exc:
        click.echo(f"Forecast error: {exc}", err=True)
        raise SystemExit(1)
