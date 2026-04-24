"""CLI commands for plateau detection."""

from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.plateau import PlateauError, detect_plateaus, format_plateaus
from cropwatch.usda_client import UsdaClient, UsdaClientError


@click.group("plateau")
def plateau_group() -> None:
    """Detect multi-week plateaus in crop progress."""


@plateau_group.command("scan")
@click.option("--commodity", "-c", required=True, help="Crop commodity name.")
@click.option("--state", "-s", default=None, help="Two-letter state abbreviation.")
@click.option(
    "--year",
    "-y",
    default=None,
    type=int,
    help="Marketing year (defaults to latest).",
)
@click.option(
    "--tolerance",
    "-t",
    default=1.0,
    type=float,
    show_default=True,
    help="Max change (pp) between weeks to be considered flat.",
)
@click.option(
    "--min-weeks",
    "-m",
    default=3,
    type=int,
    show_default=True,
    help="Minimum plateau length in weeks.",
)
def scan(
    commodity: str,
    state: str | None,
    year: int | None,
    tolerance: float,
    min_weeks: int,
) -> None:
    """Scan a commodity for multi-week flat stretches."""
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException(
            "No API key configured. Run `cropwatch config set-key <KEY>`."
        )

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(commodity=commodity, year=year, state=state)
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        plateaus = detect_plateaus(
            records,
            commodity=commodity,
            state=state,
            tolerance=tolerance,
            min_length=min_weeks,
        )
    except PlateauError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_plateaus(plateaus, commodity))
