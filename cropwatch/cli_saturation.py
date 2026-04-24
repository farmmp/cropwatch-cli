"""CLI group for saturation analysis."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.saturation import (
    SaturationError,
    detect_saturation,
    format_saturation,
    SATURATION_LOW,
    SATURATION_HIGH,
)


@click.group("saturation")
def saturation_group() -> None:
    """Detect weeks where crop progress stalls near floor or ceiling."""


@saturation_group.command("scan")
@click.option("--commodity", "-c", required=True, help="Crop commodity name.")
@click.option("--attribute", "-a", default="Value", show_default=True, help="Data attribute to inspect.")
@click.option("--state", "-s", default="US", show_default=True, help="State abbreviation.")
@click.option("--year", "-y", type=int, default=None, help="Limit to a specific year.")
@click.option("--low", type=float, default=SATURATION_LOW, show_default=True, help="Floor threshold (%).")
@click.option("--high", type=float, default=SATURATION_HIGH, show_default=True, help="Ceiling threshold (%).")
def scan(
    commodity: str,
    attribute: str,
    state: str,
    year: int | None,
    low: float,
    high: float,
) -> None:
    """Scan crop progress data for saturation weeks."""
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException("No API key configured. Run: cropwatch config set-key <key>")

    try:
        client = UsdaClient(api_key)
        records = client.get_crop_progress(commodity=commodity, year=year, state=state)
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        results = detect_saturation(
            records,
            commodity=commodity,
            attribute=attribute,
            state=state,
            low=low,
            high=high,
        )
    except SaturationError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_saturation(results, commodity))
