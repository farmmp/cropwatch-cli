"""CLI command group for seasonality analysis."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.seasonality import SeasonalityError, compute_seasonality, format_seasonality


@click.group("seasonality")
def seasonality_group() -> None:
    """Detect seasonal peak and trough weeks for a crop."""


@seasonality_group.command("peak")
@click.option("--commodity", "-c", required=True, help="Commodity name (e.g. CORN).")
@click.option("--state", "-s", default=None, help="Two-letter state abbreviation (optional).")
@click.option("--year", "-y", default=2023, show_default=True, help="Data year to query.")
@click.option("--api-key", envvar="USDA_API_KEY", default=None, hidden=True)
def show_peak(
    commodity: str,
    state: str | None,
    year: int,
    api_key: str | None,
) -> None:
    """Show the historical peak and trough weeks for a commodity."""
    key = api_key or get_api_key()
    if not key:
        click.echo("Error: No API key configured. Set USDA_API_KEY or run `cropwatch config`.")
        raise SystemExit(1)

    try:
        client = UsdaClient(api_key=key)
        records = client.get_crop_progress(commodity=commodity, year=year, state=state)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}")
        raise SystemExit(1)

    if not records:
        click.echo("No data returned from API.")
        raise SystemExit(0)

    try:
        result = compute_seasonality(records, commodity=commodity, state=state)
    except SeasonalityError as exc:
        click.echo(f"Seasonality error: {exc}")
        raise SystemExit(1)

    click.echo(format_seasonality(result))
