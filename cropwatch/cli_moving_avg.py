"""CLI commands for moving average deviation analysis."""
import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.moving_avg import compute_moving_avg, format_moving_avg, MovingAvgError


@click.group("movavg")
def movavg_group():
    """Moving average deviation commands."""


@movavg_group.command("show")
@click.option("--commodity", default="CORN", show_default=True, help="Commodity name.")
@click.option("--attribute", default="PROGRESS", show_default=True, help="Statistic category.")
@click.option("--state", default=None, help="Two-letter state abbreviation.")
@click.option("--window", default=4, show_default=True, type=int, help="Rolling window size.")
@click.option("--year", default=None, help="Crop year (default: current).")
def show_movavg(commodity, attribute, state, window, year):
    """Show moving average and deviation for a commodity attribute."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: No API key configured. Run 'cropwatch config set-key'.")
        raise SystemExit(1)

    try:
        client = UsdaClient(api_key=api_key)
        records = client.get_crop_progress(commodity=commodity, state=state, year=year)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}")
        raise SystemExit(1)

    try:
        results = compute_moving_avg(records, commodity, attribute, window=window, state=state)
    except MovingAvgError as exc:
        click.echo(f"Error: {exc}")
        raise SystemExit(1)

    click.echo(f"Moving Average (window={window}) — {commodity} / {attribute}")
    if state:
        click.echo(f"State: {state}")
    click.echo(format_moving_avg(results))
