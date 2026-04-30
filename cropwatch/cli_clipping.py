"""CLI commands for clipping detection."""
from __future__ import annotations

import click

from cropwatch.clipping import ClippingError, detect_clipping, format_clipping
from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError


@click.group("clipping")
def clipping_group() -> None:
    """Detect values stuck at 0 % or 100 % for multiple consecutive weeks."""


@clipping_group.command("scan")
@click.option("--commodity", "-c", default="CORN", show_default=True, help="Commodity name.")
@click.option("--state", "-s", default=None, help="Two-letter state abbreviation (optional).")
@click.option("--year", "-y", default=2023, show_default=True, type=int, help="Crop year.")
@click.option("--floor", default=0.0, show_default=True, type=float, help="Lower clipping boundary.")
@click.option("--ceiling", default=100.0, show_default=True, type=float, help="Upper clipping boundary.")
@click.option("--min-run", default=2, show_default=True, type=int, help="Minimum consecutive weeks to flag.")
def scan(
    commodity: str,
    state: str | None,
    year: int,
    floor: float,
    ceiling: float,
    min_run: int,
) -> None:
    """Scan for clipped values in crop progress data."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured. Run 'cropwatch config set-key'.")
        raise SystemExit(1)

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(commodity=commodity, year=year, state=state)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}")
        raise SystemExit(1)

    try:
        results = detect_clipping(
            records,
            commodity=commodity,
            state=state,
            floor=floor,
            ceiling=ceiling,
            min_consecutive=min_run,
        )
    except ClippingError as exc:
        click.echo(f"Clipping error: {exc}")
        raise SystemExit(1)

    click.echo(format_clipping(results, commodity))
