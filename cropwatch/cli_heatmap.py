"""CLI command group for state heatmap visualization."""
import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.heatmap import build_heatmap, format_heatmap, HeatmapError


@click.group("heatmap")
def heatmap_group() -> None:
    """State-level heatmap commands."""


@heatmap_group.command("show")
@click.option("--commodity", default="CORN", show_default=True, help="Crop commodity.")
@click.option("--week", required=True, help="Week ending date (YYYY-MM-DD).")
@click.option("--year", default=None, type=int, help="Crop year (defaults to current).")
@click.option("--api-key", default=None, envvar="USDA_API_KEY", help="USDA API key.")
def show_heatmap(commodity: str, week: str, year: int | None, api_key: str | None) -> None:
    """Display a state-by-value heatmap for a crop and week."""
    key = api_key or get_api_key()
    if not key:
        click.echo("Error: No API key provided. Use --api-key or set USDA_API_KEY.", err=True)
        raise SystemExit(1)
    try:
        client = UsdaClient(api_key=key)
        params: dict = {}
        if year:
            params["year"] = year
        records = client.get_crop_progress(commodity=commodity, **params)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)
    try:
        state_values = build_heatmap(records, commodity, week)
        title = f"{commodity} Progress — Week ending {week}"
        click.echo(format_heatmap(state_values, title=title))
    except HeatmapError as exc:
        click.echo(f"Heatmap error: {exc}", err=True)
        raise SystemExit(1)
