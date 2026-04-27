"""CLI command group for tapering detection."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.tapering import TaperingError, detect_tapering, format_tapering


@click.group("tapering")
def tapering_group() -> None:
    """Detect end-of-season tapering in crop progress metrics."""


@tapering_group.command("scan")
@click.option("--commodity", "-c", required=True, help="Commodity name (e.g. CORN).")
@click.option("--state", "-s", default="US", show_default=True, help="State alpha code.")
@click.option("--year", "-y", default=None, type=int, help="Marketing year (default: latest).")
@click.option("--window", "-w", default=4, show_default=True, type=int,
              help="Number of recent weeks to examine.")
@click.option("--threshold", "-t", default=5.0, show_default=True, type=float,
              help="Max weekly change (%) to qualify as tapering.")
def scan(
    commodity: str,
    state: str,
    year: int | None,
    window: int,
    threshold: float,
) -> None:
    """Scan recent weeks for a tapering pattern toward 0 % or 100 %."""
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException(
            "No API key configured. Set USDA_API_KEY or run `cropwatch config set-key`."
        )

    try:
        client = UsdaClient(api_key=api_key)
        kwargs = {"commodity": commodity, "state": state}
        if year is not None:
            kwargs["year"] = year
        records = client.get_crop_progress(**kwargs)
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        result = detect_tapering(
            records,
            commodity=commodity,
            state=state,
            window=window,
            threshold=threshold,
        )
    except TaperingError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_tapering(result, commodity=commodity, state=state))
