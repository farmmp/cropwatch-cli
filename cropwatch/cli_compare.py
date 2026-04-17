"""CLI commands for year-over-year crop progress comparison."""

import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.compare import compare_years, format_comparison, CompareError
from cropwatch.config import get_api_key


@click.group("compare")
def compare_group():
    """Compare crop progress between years."""


@compare_group.command("yoy")
@click.argument("commodity")
@click.argument("week_ending")
@click.option("--current-year", default=None, type=int, help="Current year (default: latest available).")
@click.option("--previous-year", default=None, type=int, help="Previous year (default: current-1).")
@click.option("--state", default=None, help="State abbreviation filter.")
def yoy(commodity: str, week_ending: str, current_year, previous_year, state):
    """Year-over-year comparison for COMMODITY on WEEK_ENDING (YYYY-MM-DD)."""
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException("API key not configured. Set USDA_API_KEY or run 'cropwatch config set-key'.")

    try:
        year_val = int(week_ending[:4])
    except (ValueError, IndexError):
        raise click.ClickException("WEEK_ENDING must be in YYYY-MM-DD format.")

    cur_year = current_year or year_val
    prev_year = previous_year or (cur_year - 1)

    client = UsdaClient(api_key=api_key)

    try:
        current_records = client.get_crop_progress(
            commodity=commodity.upper(), year=cur_year, state=state
        )
        previous_records = client.get_crop_progress(
            commodity=commodity.upper(), year=prev_year, state=state
        )
    except UsdaClientError as exc:
        raise click.ClickException(str(exc))

    try:
        result = compare_years(current_records, previous_records, commodity.upper(), week_ending)
    except CompareError as exc:
        raise click.ClickException(str(exc))

    click.echo(format_comparison(result))
