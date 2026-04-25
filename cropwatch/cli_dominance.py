"""CLI commands for state dominance analysis."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.dominance import compute_dominance, format_dominance, DominanceError


@click.group("dominance")
def dominance_group() -> None:
    """Identify which states dominate a crop metric."""


@dominance_group.command("top")
@click.option("--commodity", "-c", required=True, help="Commodity name (e.g. CORN).")
@click.option("--attribute", "-a", required=True, help="Attribute keyword (e.g. PROGRESS).")
@click.option("--year", "-y", default=2023, show_default=True, type=int, help="Crop year.")
@click.option("--top", "-n", default=5, show_default=True, type=int, help="Number of top states.")
@click.option("--api-key", envvar="USDA_API_KEY", default=None, help="USDA API key.")
def top(
    commodity: str,
    attribute: str,
    year: int,
    top: int,
    api_key: str | None,
) -> None:
    """Show states that most frequently lead a crop metric."""
    key = api_key or get_api_key()
    if not key:
        click.echo("Error: no API key configured.", err=True)
        raise SystemExit(1)

    try:
        client = UsdaClient(api_key=key)
        records = client.get_crop_progress(commodity=commodity, year=year)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)

    try:
        results = compute_dominance(records, commodity=commodity, attribute=attribute, top_n=top)
    except DominanceError as exc:
        click.echo(f"Dominance error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(f"State Dominance — {commodity.upper()} / {attribute} ({year})")
    click.echo(format_dominance(results))
