"""Main CLI entry point for cropwatch."""
import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.formatter import format_crop_progress, format_simple_table
from cropwatch.history import record_query
from cropwatch.cli_alerts import alerts_group
from cropwatch.cli_compare import compare_group
from cropwatch.cli_trend import trend_group


@click.group()
def cli():
    """CropWatch — USDA crop progress reports in your terminal."""


@cli.command()
@click.option("--crop", default="CORN", show_default=True, help="Crop name.")
@click.option("--state", default=None, help="State abbreviation.")
@click.option("--simple", is_flag=True, help="Simple table output.")
def progress(crop, state, simple):
    """Fetch and display current crop progress."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: No API key configured.")
        raise SystemExit(1)
    client = UsdaClient(api_key=api_key)
    try:
        data = client.get_crop_progress(commodity_desc=crop, state_alpha=state)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}")
        raise SystemExit(1)
    if not data:
        click.echo("No data returned.")
        return
    record_query(crop, state)
    if simple:
        click.echo(format_simple_table(data))
    else:
        click.echo(format_crop_progress(data))


@cli.command()
def ping():
    """Check API connectivity."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: No API key configured.")
        raise SystemExit(1)
    client = UsdaClient(api_key=api_key)
    try:
        data = client.get_crop_progress(commodity_desc="CORN")
        click.echo(f"OK — {len(data)} records fetched.")
    except UsdaClientError as exc:
        click.echo(f"FAIL — {exc}")
        raise SystemExit(1)


@cli.command("history")
def history_cmd():
    """Show recent query history."""
    from cropwatch.history import load_history
    entries = load_history()
    if not entries:
        click.echo("No history yet.")
        return
    for e in entries:
        state = e.get("state") or "national"
        click.echo(f"{e['timestamp']}  {e['crop']}  ({state})")


cli.add_command(alerts_group)
cli.add_command(compare_group)
cli.add_command(trend_group)


def main():
    cli()


if __name__ == "__main__":
    main()
