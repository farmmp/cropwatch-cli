"""CLI commands for skewness analysis."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.skewness import SkewnessError, compute_skewness, format_skewness


@click.group("skewness")
def skewness_group() -> None:
    """Skewness analysis for crop progress distributions."""


@skewness_group.command("show")
@click.option("--commodity", "-c", required=True, help="Commodity name (e.g. CORN).")
@click.option("--state", "-s", default=None, help="State abbreviation (e.g. IA).")
@click.option("--year", "-y", default=None, type=int, help="Crop year (default: latest).")
@click.option("--api-key", envvar="USDA_API_KEY", default=None, hidden=True)
def show_skewness(
    commodity: str,
    state: str | None,
    year: int | None,
    api_key: str | None,
) -> None:
    """Show skewness of crop progress values for a commodity."""
    key = api_key or get_api_key()
    if not key:
        raise click.ClickException(
            "No API key found. Set USDA_API_KEY or run `cropwatch config set-key`."
        )

    try:
        client = UsdaClient(api_key=key)
        records = client.get_crop_progress(
            commodity_desc=commodity,
            state_alpha=state,
            year=year,
        )
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        result = compute_skewness(records, commodity=commodity, state=state)
    except SkewnessError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_skewness(result))
