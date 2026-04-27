"""CLI command group for kurtosis analysis."""

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.kurtosis import compute_kurtosis, format_kurtosis, KurtosisError


@click.group("kurtosis")
def kurtosis_group() -> None:
    """Kurtosis (tail-weight) analysis of crop progress values."""


@kurtosis_group.command("show")
@click.option("--commodity", "-c", required=True, help="Commodity name (e.g. CORN).")
@click.option("--state", "-s", default="US", show_default=True, help="State alpha code.")
@click.option("--year", "-y", type=int, default=None, help="Crop year (default: latest).")
@click.option("--api-key", envvar="USDA_API_KEY", default=None, hidden=True)
def show_kurtosis(
    commodity: str,
    state: str,
    year: int | None,
    api_key: str | None,
) -> None:
    """Display excess kurtosis for a commodity's weekly progress values."""
    key = api_key or get_api_key()
    if not key:
        raise click.ClickException(
            "No API key found. Set USDA_API_KEY or run: cropwatch config set-key"
        )

    try:
        client = UsdaClient(api_key=key)
        records = client.get_crop_progress(commodity=commodity, year=year, state=state)
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        result = compute_kurtosis(records, commodity=commodity, state=state)
    except KurtosisError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_kurtosis(result))
