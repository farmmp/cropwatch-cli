"""CLI command group for lead-lag analysis."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.leadlag import LeadLagError, compute_leadlag, format_leadlag


@click.group("leadlag")
def leadlag_group() -> None:
    """Lead-lag analysis between two commodities."""


@leadlag_group.command("compare")
@click.option("--commodity-a", required=True, help="First commodity (e.g. CORN).")
@click.option("--commodity-b", required=True, help="Second commodity (e.g. SOYBEANS).")
@click.option("--year", default=2023, show_default=True, type=int, help="Crop year.")
@click.option("--state", default=None, help="Filter by state abbreviation.")
@click.option(
    "--max-lag",
    default=4,
    show_default=True,
    type=int,
    help="Maximum lag in weeks to test.",
)
@click.option("--api-key", default=None, help="USDA API key (overrides config/env).")
def compare(
    commodity_a: str,
    commodity_b: str,
    year: int,
    state: str | None,
    max_lag: int,
    api_key: str | None,
) -> None:
    """Find the week offset where two commodities are most correlated."""
    key = api_key or get_api_key()
    if not key:
        raise click.ClickException(
            "No API key found. Set USDA_API_KEY or run `cropwatch config set-key`."
        )

    client = UsdaClient(api_key=key)
    try:
        records_a = client.get_crop_progress(
            commodity_desc=commodity_a, year=year, state_alpha=state
        )
        records_b = client.get_crop_progress(
            commodity_desc=commodity_b, year=year, state_alpha=state
        )
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc

    all_records = records_a + records_b
    try:
        result = compute_leadlag(
            all_records,
            commodity_a=commodity_a,
            commodity_b=commodity_b,
            state=state,
            max_lag=max_lag,
        )
    except LeadLagError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_leadlag(result))
