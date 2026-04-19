"""CLI commands for percentile ranking of crop progress."""
import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.percentile import compute_percentiles, format_percentiles, PercentileError


@click.group("percentile")
def percentile_group():
    """Percentile ranking of crop progress across states."""


@percentile_group.command("rank")
@click.option("--commodity", "-c", default="corn", show_default=True, help="Crop commodity.")
@click.option("--week", "-w", required=True, help="Week ending date (YYYY-MM-DD).")
@click.option("--year", "-y", default=None, type=int, help="Crop year (default: latest).")
@click.option("--attribute", "-a", default="Value", show_default=True, help="Data attribute.")
def rank(commodity: str, week: str, year: int | None, attribute: str):
    """Show percentile ranking of states for a commodity and week."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: No API key configured. Set USDA_API_KEY or run `cropwatch config`.")
        raise SystemExit(1)

    try:
        client = UsdaClient(api_key=api_key)
        params = {}
        if year:
            params["year"] = year
        records = client.get_crop_progress(commodity=commodity, **params)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}")
        raise SystemExit(1)

    try:
        results = compute_percentiles(records, commodity=commodity, week_ending=week, attribute=attribute)
    except PercentileError as exc:
        click.echo(f"Percentile error: {exc}")
        raise SystemExit(1)

    click.echo(format_percentiles(results, commodity=commodity, week_ending=week))
