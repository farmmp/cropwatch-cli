"""CLI command group for z-score outlier ranking."""

from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.zscore import ZScoreError, compute_zscores, format_zscores


@click.group(name="zscore")
def zscore_group() -> None:
    """Z-score outlier ranking for crop progress values."""


@zscore_group.command(name="rank")
@click.option("--commodity", "-c", default="CORN", show_default=True, help="Commodity name.")
@click.option("--attribute", "-a", default="CORN, GRAIN - PROGRESS, MEASURED IN PCT HARVESTED",
              show_default=True, help="Short description / attribute to analyse.")
@click.option("--state", "-s", default=None, help="Restrict to a single state name.")
@click.option("--year", "-y", default=None, type=int, help="Crop year (defaults to latest).")
@click.option("--top", "-n", default=10, show_default=True, type=int, help="Number of rows to show.")
def rank(
    commodity: str,
    attribute: str,
    state: str | None,
    year: int | None,
    top: int,
) -> None:
    """Rank weeks by how far their value deviates from the mean (z-score)."""
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException(
            "No API key configured. Set USDA_API_KEY or run: cropwatch config set-key"
        )

    try:
        client = UsdaClient(api_key=api_key)
        records = client.get_crop_progress(
            commodity_desc=commodity,
            year=year,
            state_name=state,
        )
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        results = compute_zscores(records, commodity=commodity, attribute=attribute, state=state)
    except ZScoreError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Z-Score Outlier Ranking — {commodity}  |  {attribute}")
    if state:
        click.echo(f"State: {state}")
    click.echo()
    click.echo(format_zscores(results, top_n=top))
