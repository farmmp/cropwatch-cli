"""Main CLI entry-point for cropwatch."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key, load_config, save_config
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.formatter import format_crop_progress, format_simple_table
from cropwatch.history import record_query, load_history
from cropwatch.cli_alerts import alerts_group
from cropwatch.cli_compare import compare_group
from cropwatch.cli_trend import trend_group
from cropwatch.cli_forecast import forecast_group


@click.group()
def cli():
    """CropWatch — USDA crop progress reports in your terminal."""


@cli.command()
@click.option("--commodity", "-c", default="Corn", show_default=True)
@click.option("--year", "-y", default=2024, show_default=True, type=int)
@click.option("--state", "-s", default=None)
@click.option("--simple", is_flag=True, default=False, help="Plain table output.")
@click.option("--api-key", envvar="USDA_API_KEY", default=None, hidden=True)
def progress(commodity, year, state, simple, api_key):
    """Fetch and display the latest crop progress report."""
    key = api_key or get_api_key()
    if not key:
        click.echo("Error: No API key configured.", err=True)
        raise SystemExit(1)
    try:
        client = UsdaClient(api_key=key)
        kwargs = {"year": year, "commodity_desc": commodity}
        if state:
            kwargs["state_alpha"] = state.upper()
        data = client.get_crop_progress(**kwargs)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)
    if not data:
        click.echo("No data returned.")
        return
    record_query(commodity=commodity, year=year, state=state)
    if simple:
        click.echo(format_simple_table(data))
    else:
        click.echo(format_crop_progress(data))


@cli.command()
@click.option("--api-key", envvar="USDA_API_KEY", default=None, hidden=True)
def ping(api_key):
    """Check connectivity to the USDA NASS API."""
    key = api_key or get_api_key()
    if not key:
        click.echo("Error: No API key configured.", err=True)
        raise SystemExit(1)
    try:
        client = UsdaClient(api_key=key)
        client.get_crop_progress(year=2024, commodity_desc="Corn")
        click.echo("OK — USDA API is reachable.")
    except UsdaClientError as exc:
        click.echo(f"FAILED: {exc}", err=True)
        raise SystemExit(1)


@cli.command(name="history")
@click.option("--limit", default=10, show_default=True, type=int)
def history_cmd(limit):
    """Show recent query history."""
    entries = load_history()[-limit:]
    if not entries:
        click.echo("No history yet.")
        return
    for e in reversed(entries):
        state_part = f" [{e.get('state')}]" if e.get("state") else ""
        click.echo(f"{e.get('timestamp', '?')[:19]}  {e.get('commodity')} {e.get('year')}{state_part}")


cli.add_command(alerts_group, name="alerts")
cli.add_command(compare_group, name="compare")
cli.add_command(trend_group, name="trend")
cli.add_command(forecast_group, name="forecast")


def main():
    cli()


if __name__ == "__main__":
    main()
