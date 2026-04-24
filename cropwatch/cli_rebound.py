"""CLI command group for rebound detection."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.rebound import detect_rebounds, format_rebounds, ReboundError


@click.group("rebound")
def rebound_group() -> None:
    """Detect rebound patterns in crop progress data."""


@rebound_group.command("scan")
@click.option("--commodity", "-c", default="CORN", show_default=True, help="Commodity name.")
@click.option("--state", "-s", default="US", show_default=True, help="State alpha code.")
@click.option("--year", "-y", default=2023, show_default=True, type=int, help="Crop year.")
@click.option(
    "--min-depth",
    "-d",
    default=2.0,
    show_default=True,
    type=float,
    help="Minimum dip depth (percentage points) to qualify as a rebound.",
)
def scan(
    commodity: str,
    state: str,
    year: int,
    min_depth: float,
) -> None:
    """Scan for rebound events where progress dips then surpasses the prior level."""
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException(
            "No API key configured. Set USDA_API_KEY or run `cropwatch config set-key`."
        )
    try:
        client = UsdaClient(api_key=api_key)
        records = client.get_crop_progress(commodity=commodity, year=year, state=state)
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        results = detect_rebounds(
            records, commodity=commodity.upper(), state=state.upper(), min_depth=min_depth
        )
    except ReboundError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_rebounds(results, commodity=commodity.upper(), state=state.upper()))
