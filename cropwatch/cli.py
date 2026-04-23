"""Main CLI entry-point for cropwatch."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key, save_config
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.formatter import format_crop_progress, format_simple_table
from cropwatch.history import record_query, load_history
from cropwatch.export import export_data, write_export, ExportError
from cropwatch.cli_alerts import alerts_group
from cropwatch.cli_compare import compare_group
from cropwatch.cli_trend import trend_group
from cropwatch.cli_forecast import forecast_group
from cropwatch.cli_anomaly import anomaly_group
from cropwatch.cli_heatmap import heatmap_group
from cropwatch.cli_correlation import correlation_group
from cropwatch.cli_percentile import percentile_group
from cropwatch.cli_baseline import baseline_group
from cropwatch.cli_seasonavg import seasonavg_group
from cropwatch.cli_smooth import smooth_group
from cropwatch.cli_moving_avg import movavg_group
from cropwatch.cli_volatility import volatility_group


@click.group()
def cli() -> None:
    """CropWatch — USDA crop progress in your terminal."""


cli.add_command(alerts_group, "alerts")
cli.add_command(compare_group, "compare")
cli.add_command(trend_group, "trend")
cli.add_command(forecast_group, "forecast")
cli.add_command(anomaly_group, "anomaly")
cli.add_command(heatmap_group, "heatmap")
cli.add_command(correlation_group, "correlation")
cli.add_command(percentile_group, "percentile")
cli.add_command(baseline_group, "baseline")
cli.add_command(seasonavg_group, "seasonavg")
cli.add_command(smooth_group, "smooth")
cli.add_command(movavg_group, "movavg")
cli.add_command(volatility_group, "volatility")


@cli.command()
@click.option("--commodity", "-c", default="CORN", show_default=True)
@click.option("--state", "-s", default=None)
@click.option("--year", "-y", default=None, type=int)
@click.option("--simple", is_flag=True, default=False, help="Plain table output.")
def progress(commodity: str, state: str | None, year: int | None, simple: bool) -> None:
    """Fetch and display crop progress data."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured. Run `cropwatch config set-key`.")
        raise SystemExit(1)
    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(commodity=commodity, state=state, year=year)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}")
        raise SystemExit(1)
    if not records:
        click.echo("No data returned.")
        return
    record_query(commodity=commodity, state=state, year=year)
    click.echo(format_simple_table(records) if simple else format_crop_progress(records))


@cli.command()
def ping() -> None:
    """Check API connectivity."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured.")
        raise SystemExit(1)
    client = UsdaClient(api_key=api_key)
    try:
        client.get_crop_progress(commodity="CORN", year=2023)
        click.echo("OK — USDA NASS API is reachable.")
    except UsdaClientError as exc:
        click.echo(f"FAILED: {exc}")
        raise SystemExit(1)


@cli.command(name="history")
@click.option("--limit", default=10, show_default=True, type=int)
def history_cmd(limit: int) -> None:
    """Show recent query history."""
    entries = load_history()[-limit:]
    if not entries:
        click.echo("No history yet.")
        return
    for entry in reversed(entries):
        parts = [entry.get("timestamp", ""), entry.get("commodity", "")]
        if entry.get("state"):
            parts.append(entry["state"])
        if entry.get("year"):
            parts.append(str(entry["year"]))
        click.echo("  ".join(parts))


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
