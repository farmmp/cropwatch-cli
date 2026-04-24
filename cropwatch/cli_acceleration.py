"""CLI commands for crop progress acceleration analysis.

Acceleration measures the rate of change of the rate of change —
how quickly progress is speeding up or slowing down week over week.
"""

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.acceleration import compute_acceleration, format_acceleration, AccelerationError


@click.group("acceleration")
def acceleration_group() -> None:
    """Analyze acceleration (2nd derivative) of crop progress."""


@acceleration_group.command("show")
@click.option("--commodity", "-c", required=True, help="Commodity name (e.g. 'Corn').")
@click.option("--state", "-s", default=None, help="State abbreviation filter (e.g. 'IA'). Defaults to national.")
@click.option("--year", "-y", required=True, type=int, help="Crop year to analyze.")
@click.option(
    "--threshold",
    "-t",
    default=5.0,
    show_default=True,
    type=float,
    help="Minimum absolute acceleration (pp/week²) to highlight.",
)
def show_acceleration(
    commodity: str,
    state: str | None,
    year: int,
    threshold: float,
) -> None:
    """Show week-over-week acceleration of crop progress.

    Acceleration is computed as the difference between consecutive
    weekly changes (i.e. the second discrete derivative of progress).
    Positive values indicate the pace of improvement is increasing;
    negative values indicate it is slowing.

    Example:

        cropwatch acceleration show -c Corn -y 2023 -t 3.0
    """
    api_key = get_api_key()
    if not api_key:
        click.echo(
            "Error: No API key configured. "
            "Set USDA_API_KEY or run 'cropwatch config set-key <key>'.",
            err=True,
        )
        raise SystemExit(1)

    client = UsdaClient(api_key=api_key)

    try:
        records = client.get_crop_progress(commodity=commodity, year=year, state=state)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)

    if not records:
        click.echo("No data returned for the given parameters.")
        return

    try:
        result = compute_acceleration(
            records=records,
            commodity=commodity,
            state=state,
            threshold=threshold,
        )
    except AccelerationError as exc:
        click.echo(f"Acceleration error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(format_acceleration(result))
