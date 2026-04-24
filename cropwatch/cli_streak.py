"""CLI command group for streak detection."""
from __future__ import annotations

import click

from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.streak import detect_streak, format_streak, StreakError


@click.group("streak")
def streak_group() -> None:
    """Detect consecutive up/down streaks in crop progress."""


@streak_group.command("longest")
@click.option("--commodity", "-c", required=True, help="Commodity name (e.g. CORN).")
@click.option("--state", "-s", default=None, help="Two-letter state abbreviation (default: US).")
@click.option("--year", "-y", required=True, type=int, help="Survey year.")
@click.option(
    "--desc",
    "-d",
    default="PROGRESS, MEASURED IN PCT EXCELLENT",
    show_default=True,
    help="Short description filter.",
)
def longest(commodity: str, state: str | None, year: int, desc: str) -> None:
    """Show the longest consecutive up or down streak for a commodity."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured. Run `cropwatch ping` or set USDA_API_KEY.", err=True)
        raise SystemExit(1)

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(
            commodity_desc=commodity,
            state_alpha=state,
            year=year,
            short_desc=desc,
        )
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)

    if not records:
        click.echo("No data returned for the given parameters.")
        return

    try:
        result = detect_streak(records, commodity=commodity, state=state)
    except StreakError as exc:
        click.echo(f"Streak error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(format_streak(result))
