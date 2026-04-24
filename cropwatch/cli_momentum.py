"""CLI command group for momentum analysis.

Exposes the `momentum` subcommand which computes week-over-week
acceleration of crop progress values for a given commodity.
"""

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.momentum import compute_momentum, format_momentum, MomentumError


@click.group(name="momentum")
def momentum_group() -> None:
    """Analyse week-over-week momentum in crop progress."""


@momentum_group.command(name="show")
@click.option(
    "--commodity",
    default="CORN",
    show_default=True,
    help="Commodity name to analyse (e.g. CORN, SOYBEANS).",
)
@click.option(
    "--state",
    default=None,
    help="Limit analysis to a specific state abbreviation (e.g. IA).",
)
@click.option(
    "--year",
    default=2024,
    show_default=True,
    type=int,
    help="Crop year to fetch.",
)
@click.option(
    "--week",
    default=None,
    type=int,
    help="Restrict output to a specific week number.",
)
@click.option(
    "--top",
    default=None,
    type=int,
    help="Show only the top N results by absolute momentum.",
)
def show_momentum(
    commodity: str,
    state: str | None,
    year: int,
    week: int | None,
    top: int | None,
) -> None:
    """Display week-over-week momentum for a crop commodity.

    Momentum is defined as the change in the rate-of-change between
    consecutive weeks, highlighting acceleration or deceleration in
    progress reports.
    """
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

    if not records:
        click.echo("No data returned for the given parameters.")
        return

    try:
        results = compute_momentum(records, commodity=commodity, state=state)
    except MomentumError as exc:
        raise click.ClickException(str(exc)) from exc

    # Optional week filter
    if week is not None:
        results = [r for r in results if r.week == week]

    # Optional top-N filter by absolute momentum value
    if top is not None:
        results = sorted(results, key=lambda r: abs(r.momentum), reverse=True)[:top]

    if not results:
        click.echo("No momentum data matched the given filters.")
        return

    click.echo(format_momentum(results))
