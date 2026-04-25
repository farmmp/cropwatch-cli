"""CLI group for the concentration (HHI) command."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.concentration import (
    ConcentrationError,
    compute_concentration,
    format_concentration,
)


@click.group("concentration")
def concentration_group() -> None:
    """Compute market-concentration (HHI) across states."""


@concentration_group.command("hhi")
@click.option("--commodity", "-c", default="CORN", show_default=True, help="Commodity name.")
@click.option("--week", "-w", required=True, help="Week ending date (YYYY-MM-DD) or week_desc.")
@click.option("--year", "-y", default=2023, show_default=True, type=int, help="Survey year.")
def hhi(commodity: str, week: str, year: int) -> None:
    """Show HHI concentration for a commodity in a given week."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured. Set USDA_API_KEY or run `cropwatch config`.")
        raise SystemExit(1)

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(commodity=commodity, year=year)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}")
        raise SystemExit(1)

    try:
        result = compute_concentration(records, commodity=commodity, week_desc=week)
    except ConcentrationError as exc:
        click.echo(f"Concentration error: {exc}")
        raise SystemExit(1)

    click.echo(format_concentration(result))
