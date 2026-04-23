"""CLI commands for crop-progress volatility analysis."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.volatility import VolatilityError, compute_volatility, format_volatility


@click.group("volatility")
def volatility_group() -> None:
    """Analyse week-over-week volatility in crop progress data."""


@volatility_group.command("show")
@click.option("--commodity", "-c", default="CORN", show_default=True, help="Commodity name.")
@click.option("--attribute", "-a", default="PROGRESS, MEASURED IN PCT PLANTED", show_default=True, help="Short-desc substring to match.")
@click.option("--state", "-s", default=None, help="Two-letter state abbreviation (omit for national).")
@click.option("--year", "-y", default=None, type=int, help="Limit to a single year.")
def show_volatility(
    commodity: str,
    attribute: str,
    state: str | None,
    year: int | None,
) -> None:
    """Show volatility statistics for a commodity/attribute series."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured. Run `cropwatch config set-key`.")
        raise SystemExit(1)

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(commodity=commodity, state=state, year=year)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}")
        raise SystemExit(1)

    try:
        result = compute_volatility(records, commodity=commodity, attribute=attribute, state=state)
    except VolatilityError as exc:
        click.echo(f"Volatility error: {exc}")
        raise SystemExit(1)

    click.echo(format_volatility(result))
