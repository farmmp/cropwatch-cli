"""CLI command group for inflection-point detection."""

from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.inflection import InflectionError, detect_inflections, format_inflections
from cropwatch.usda_client import UsdaClient, UsdaClientError


@click.group("inflection")
def inflection_group() -> None:
    """Detect trend reversals in crop progress data."""


@inflection_group.command("scan")
@click.option("--commodity", "-c", default="CORN", show_default=True, help="Commodity name.")
@click.option("--state", "-s", default=None, help="Two-letter state abbreviation (optional).")
@click.option("--year", "-y", default=2023, show_default=True, type=int, help="Crop year.")
@click.option(
    "--min-change",
    "-m",
    default=2.0,
    show_default=True,
    type=float,
    help="Minimum week-over-week change to qualify as a direction shift.",
)
def scan(
    commodity: str,
    state: str | None,
    year: int,
    min_change: float,
) -> None:
    """Scan a crop series for inflection points (trend reversals)."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured. Run `cropwatch ping` or set USDA_API_KEY.", err=True)
        raise SystemExit(1)

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(commodity=commodity, year=year, state=state)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)

    try:
        points = detect_inflections(records, commodity=commodity, state=state, min_change=min_change)
    except InflectionError as exc:
        click.echo(f"Inflection error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(format_inflections(points, commodity=commodity))
