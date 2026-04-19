"""CLI command group for seasonal average."""
import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.seasonavg import compute_season_avg, format_season_avg, SeasonAvgError


@click.group("seasonavg")
def seasonavg_group() -> None:
    """Seasonal average commands."""


@seasonavg_group.command("show")
@click.option("--commodity", default="CORN", show_default=True, help="Crop commodity")
@click.option("--state", default="US", show_default=True, help="State alpha code")
@click.option("--year", required=True, type=int, help="Season year")
@click.option("--value-key", default="Value", show_default=True, help="Field to average")
def show_season_avg(
    commodity: str, state: str, year: int, value_key: str
) -> None:
    """Display seasonal average stats for a commodity."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured.", err=True)
        raise SystemExit(1)

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(
            commodity=commodity, year=year, state=state if state != "US" else None
        )
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)

    try:
        result = compute_season_avg(records, commodity=commodity, state=state, value_key=value_key)
    except SeasonAvgError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(format_season_avg(result))
