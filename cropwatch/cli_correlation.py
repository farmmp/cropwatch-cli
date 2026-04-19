"""CLI commands for crop correlation analysis."""
import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.correlation import correlate, format_correlation, CorrelationError


@click.group("correlate")
def correlation_group():
    """Compare progress trends between two commodities."""


@correlation_group.command("run")
@click.option("--commodity-a", required=True, help="First commodity (e.g. CORN).")
@click.option("--commodity-b", required=True, help="Second commodity (e.g. SOYBEANS).")
@click.option("--year", default=None, type=int, help="Crop year (default: latest).")
@click.option("--state", default=None, help="State abbreviation filter.")
@click.option("--api-key", default=None, envvar="USDA_API_KEY", help="USDA API key.")
def run_correlation(commodity_a, commodity_b, year, state, api_key):
    """Compute Pearson correlation between two commodities."""
    key = api_key or get_api_key()
    if not key:
        click.echo("Error: No API key provided. Set USDA_API_KEY or use --api-key.", err=True)
        raise SystemExit(1)
    try:
        client = UsdaClient(api_key=key)
        records_a = client.get_crop_progress(commodity=commodity_a, year=year, state=state)
        records_b = client.get_crop_progress(commodity=commodity_b, year=year, state=state)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)
    combined = records_a + records_b
    try:
        result = correlate(combined, commodity_a, commodity_b)
    except CorrelationError as exc:
        click.echo(f"Correlation error: {exc}", err=True)
        raise SystemExit(1)
    click.echo(format_correlation(result))
