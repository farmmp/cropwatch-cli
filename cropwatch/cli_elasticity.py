"""CLI commands for the elasticity feature."""
import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.elasticity import compute_elasticity, format_elasticity, ElasticityError


@click.group("elasticity")
def elasticity_group() -> None:
    """Measure week-over-week percentage sensitivity of crop progress."""


@elasticity_group.command("show")
@click.option("--commodity", "-c", required=True, help="Commodity name (e.g. CORN).")
@click.option("--state", "-s", default="US", show_default=True, help="State alpha code.")
@click.option("--year", "-y", type=int, default=None, help="Crop year (default: latest).")
@click.option("--api-key", envvar="USDA_API_KEY", default=None, help="USDA API key.")
def show_elasticity(
    commodity: str,
    state: str,
    year: int,
    api_key: str,
) -> None:
    """Show week-over-week elasticity (% change) for a commodity."""
    key = api_key or get_api_key()
    if not key:
        raise click.ClickException(
            "No API key found. Set USDA_API_KEY or run: cropwatch config set-key <key>"
        )

    client = UsdaClient(api_key=key)
    try:
        records = client.get_crop_progress(commodity=commodity, year=year, state=state)
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        result = compute_elasticity(records, commodity=commodity, state=state)
    except ElasticityError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_elasticity(result))
