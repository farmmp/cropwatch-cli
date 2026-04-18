"""Main CLI entry point for cropwatch."""
import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.formatter import format_crop_progress, format_simple_table
from cropwatch.cli_alerts import alerts_group
from cropwatch.cli_compare import compare_group
from cropwatch.cli_trend import trend_group
from cropwatch.cli_forecast import forecast_group
from cropwatch.cli_anomaly import anomaly_group


@click.group()
def cli():
    """CropWatch — USDA crop progress in your terminal."""


@cli.command()
@click.option("--crop", default="corn", show_default=True)
@click.option("--state", default=None)
@click.option("--year", default=2023, show_default=True, type=int)
@click.option("--simple", is_flag=True, default=False)
def progress(crop, state, year, simple):
    """Fetch and display crop progress."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: No API key configured.", err=True)
        raise SystemExit(1)
    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(crop=crop, year=year, state=state)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)
    if not records:
        click.echo("No data returned.")
        return
    if simple:
        click.echo(format_simple_table(records))
    else:
        click.echo(format_crop_progress(records, crop=crop, year=year))


@cli.command()
def ping():
    """Check API connectivity."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: No API key configured.", err=True)
        raise SystemExit(1)
    click.echo("OK")


@cli.command("history")
def history_cmd():
    """Show recent query history."""
    from cropwatch.history import load_history
    rows = load_history()
    if not rows:
        click.echo("No history yet.")
        return
    for row in rows:
        click.echo(row)


cli.add_command(alerts_group)
cli.add_command(compare_group)
cli.add_command(trend_group)
cli.add_command(forecast_group)
cli.add_command(anomaly_group)


def main():
    cli()


if __name__ == "__main__":
    main()
