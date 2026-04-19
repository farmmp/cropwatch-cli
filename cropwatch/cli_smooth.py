"""CLI command group for rolling-average smoothing."""
import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.smooth import smooth_series, format_smooth, SmoothError


@click.group("smooth")
def smooth_group():
    """Smooth crop progress data with a rolling average."""


@smooth_group.command("show")
@click.option("--commodity", "-c", required=True, help="Commodity name (e.g. CORN).")
@click.option("--year", "-y", required=True, type=int, help="Crop year.")
@click.option("--state", "-s", default=None, help="State abbreviation (optional).")
@click.option("--window", "-w", default=3, show_default=True, type=int, help="Rolling window size.")
@click.option("--api-key", envvar="USDA_API_KEY", default=None, hidden=True)
def show_smooth(commodity, year, state, window, api_key):
    """Display a rolling-average smoothed series for a commodity."""
    key = api_key or get_api_key()
    if not key:
        click.echo("Error: No API key configured. Set USDA_API_KEY or run 'cropwatch config set-key'.")
        raise SystemExit(1)

    try:
        client = UsdaClient(api_key=key)
        records = client.get_crop_progress(year=year, state=state)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}")
        raise SystemExit(1)

    try:
        series = smooth_series(records, commodity=commodity, window=window)
    except SmoothError as exc:
        click.echo(f"Smooth error: {exc}")
        raise SystemExit(1)

    click.echo(format_smooth(series, commodity))
