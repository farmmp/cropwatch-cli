"""CLI commands for regime-shift detection."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.regime import RegimeError, detect_regimes, format_regimes


@click.group("regime")
def regime_group() -> None:
    """Detect sustained regime shifts in crop progress."""


@regime_group.command("scan")
@click.option("--commodity", "-c", required=True, help="Commodity name, e.g. CORN")
@click.option("--state", "-s", default=None, help="State abbreviation, e.g. IA")
@click.option(
    "--year",
    "-y",
    default=None,
    type=int,
    help="Marketing year (defaults to latest).",
)
@click.option(
    "--threshold",
    "-t",
    default=0.0,
    type=float,
    show_default=True,
    help="Dead-zone around mean (percentage points).",
)
@click.option("--shifts-only", is_flag=True, default=False, help="Print only shift rows.")
def scan(
    commodity: str,
    state: str | None,
    year: int | None,
    threshold: float,
    shifts_only: bool,
) -> None:
    """Scan a crop progress series for regime shifts."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured. Run `cropwatch ping` or set USDA_API_KEY.", err=True)
        raise SystemExit(1)

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(commodity=commodity, state=state, year=year)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)

    try:
        results = detect_regimes(records, commodity=commodity, state=state, threshold=threshold)
    except RegimeError as exc:
        click.echo(f"Regime error: {exc}", err=True)
        raise SystemExit(1)

    if shifts_only:
        results = [r for r in results if r.shift]
        if not results:
            click.echo("No regime shifts detected.")
            return

    click.echo(format_regimes(results))
