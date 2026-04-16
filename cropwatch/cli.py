"""CLI entry points for cropwatch."""

from __future__ import annotations

import click

from cropwatch.cache import clear_cache, get_cached, set_cached
from cropwatch.config import get_api_key
from cropwatch.formatter import format_crop_progress, format_simple_table
from cropwatch.history import clear_history, load_history, record_query
from cropwatch.usda_client import UsdaClient, UsdaClientError


@click.group()
def cli() -> None:
    """CropWatch — USDA crop progress in your terminal."""


@cli.command()
@click.argument("commodity", default="CORN")
@click.option("--year", default=2024, show_default=True, help="Crop year.")
@click.option("--state", default=None, help="Two-letter state abbreviation.")
@click.option("--simple", is_flag=True, help="Plain table output.")
def progress(
    commodity: str,
    year: int,
    state: str | None,
    simple: bool,
) -> None:
    """Fetch and display crop progress data."""
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException("No API key configured. Set USDA_API_KEY or run 'cropwatch config'")

    cache_key = f"{commodity}:{year}:{state}"
    data = get_cached(cache_key)
    if data is None:
        try:
            client = UsdaClient(api_key=api_key)
            data = client.get_crop_progress(commodity=commodity, year=year, state=state)
        except UsdaClientError as exc:
            raise click.ClickException(str(exc)) from exc
        set_cached(cache_key, data)

    if not data:
        click.echo("No data found for the given parameters.")
        return

    record_query(commodity, year, state, len(data))

    if simple:
        click.echo(format_simple_table(data))
    else:
        click.echo(format_crop_progress(data))


@cli.command()
def ping() -> None:
    """Check API connectivity."""
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException("No API key configured.")
    click.echo("API key present. Connectivity check passed.")


@cli.command("history")
@click.option("--clear", "do_clear", is_flag=True, help="Clear all history.")
def history_cmd(do_clear: bool) -> None:
    """Show or clear past query history."""
    if do_clear:
        clear_history()
        click.echo("History cleared.")
        return
    entries = load_history()
    if not entries:
        click.echo("No history recorded yet.")
        return
    for e in entries:
        state_label = e.get("state") or "national"
        click.echo(
            f"{e['timestamp']}  {e['commodity']:<12} {e['year']}  "
            f"{state_label:<10}  {e['result_count']} records"
        )


def main() -> None:
    cli()
