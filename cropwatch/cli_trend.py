"""CLI commands for crop progress trend visualization."""
import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.sparkline import format_trend_table, SparklineError


@click.group("trend")
def trend_group():
    """Trend visualization commands."""


@trend_group.command("show")
@click.option("--crop", default="CORN", show_default=True, help="Crop name.")
@click.option("--state", default=None, help="State abbreviation (e.g. IA).")
@click.option("--commodity-desc", default="CORN", hidden=True)
@click.option(
    "--statisticcat-desc",
    default="PROGRESS",
    show_default=True,
    help="Statistic category.",
)
@click.option("--year", default=None, help="Filter by year (e.g. 2023).")
def show_trend(crop, state, commodity_desc, statisticcat_desc, year):
    """Show a sparkline trend for crop progress."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: No API key configured. Set USDA_API_KEY or run 'cropwatch config'.")
        raise SystemExit(1)

    client = UsdaClient(api_key=api_key)
    params = {}
    if year:
        params["year"] = year
    if state:
        params["state_alpha"] = state

    try:
        data = client.get_crop_progress(
            commodity_desc=crop,
            statisticcat_desc=statisticcat_desc,
            **params,
        )
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}")
        raise SystemExit(1)

    if not data:
        click.echo("No data returned.")
        return

    try:
        output = format_trend_table(data)
    except SparklineError as exc:
        click.echo(f"Sparkline error: {exc}")
        raise SystemExit(1)

    click.echo(output)
