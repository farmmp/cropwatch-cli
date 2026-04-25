"""CLI commands for week-over-week transition detection."""
import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.transition import TransitionError, detect_transitions, format_transitions


@click.group("transition")
def transition_group() -> None:
    """Detect week-over-week value transitions for a commodity."""


@transition_group.command("scan")
@click.option("--commodity", "-c", required=True, help="Commodity name (e.g. CORN).")
@click.option("--state", "-s", default="US", show_default=True, help="State alpha code.")
@click.option("--year", "-y", default=2023, show_default=True, type=int, help="Survey year.")
@click.option(
    "--threshold",
    "-t",
    default=0.0,
    show_default=True,
    type=float,
    help="Min change to count as up/down (percentage points).",
)
def scan(
    commodity: str,
    state: str,
    year: int,
    threshold: float,
) -> None:
    """Show week-over-week transitions for a commodity/state/year."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured. Run `cropwatch ping` or set USDA_API_KEY.", err=True)
        raise SystemExit(1)

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(commodity=commodity, year=year, state=state)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)

    try:
        result = detect_transitions(records, commodity=commodity, state=state, threshold=threshold)
    except TransitionError as exc:
        click.echo(f"Transition error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(format_transitions(result))
