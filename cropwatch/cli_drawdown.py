"""CLI commands for drawdown analysis."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.drawdown import DrawdownError, compute_drawdown, format_drawdown
from cropwatch.usda_client import UsdaClient, UsdaClientError


@click.group("drawdown")
def drawdown_group() -> None:
    """Detect peak-to-trough drawdowns in crop progress."""


@drawdown_group.command("scan")
@click.option("--commodity", "-c", default="CORN", show_default=True, help="Commodity name.")
@click.option("--state", "-s", default="US", show_default=True, help="State abbreviation.")
@click.option("--year", "-y", default=None, type=int, help="Crop year (default: latest).")
@click.option(
    "--attribute",
    "-a",
    default="PROGRESS",
    show_default=True,
    help="Statistic category (e.g. PROGRESS, CONDITION).",
)
def scan(
    commodity: str,
    state: str,
    year: int | None,
    attribute: str,
) -> None:
    """Scan for the maximum drawdown over a season."""
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException(
            "No API key configured. Set USDA_API_KEY or run `cropwatch config set-key`."
        )

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(
            commodity=commodity,
            year=year,
            state=state if state.upper() != "US" else None,
        )
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        result = compute_drawdown(records, commodity=commodity, state=state, attribute=attribute)
    except DrawdownError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_drawdown(result))
