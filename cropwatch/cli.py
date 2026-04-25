"""Main CLI entry-point for cropwatch."""
from __future__ import annotations

import click

from cropwatch.config import get_api_key, load_config, save_config
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.formatter import format_crop_progress, format_simple_table
from cropwatch.history import record_query, load_history
from cropwatch.cache import get_cached, set_cached
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
from cropwatch.cli_momentum import momentum_group
from cropwatch.cli_saturation import saturation_group
from cropwatch.cli_streak import streak_group
from cropwatch.cli_rebound import rebound_group
from cropwatch.cli_plateau import plateau_group
from cropwatch.cli_acceleration import acceleration_group
from cropwatch.cli_seasonality import seasonality_group
from cropwatch.cli_drawdown import drawdown_group
from cropwatch.cli_inflection import inflection_group
from cropwatch.cli_regime import regime_group


@click.group()
def cli() -> None:
    """CropWatch — USDA crop progress in your terminal."""


# ── sub-command groups ──────────────────────────────────────────────────────
cli.add_command(alerts_group, name="alerts")
cli.add_command(compare_group, name="compare")
cli.add_command(trend_group, name="trend")
cli.add_command(forecast_group, name="forecast")
cli.add_command(anomaly_group, name="anomaly")
cli.add_command(heatmap_group, name="heatmap")
cli.add_command(correlation_group, name="correlation")
cli.add_command(percentile_group, name="percentile")
cli.add_command(baseline_group, name="baseline")
cli.add_command(seasonavg_group, name="seasonavg")
cli.add_command(smooth_group, name="smooth")
cli.add_command(movavg_group, name="movavg")
cli.add_command(volatility_group, name="volatility")
cli.add_command(momentum_group, name="momentum")
cli.add_command(saturation_group, name="saturation")
cli.add_command(streak_group, name="streak")
cli.add_command(rebound_group, name="rebound")
cli.add_command(plateau_group, name="plateau")
cli.add_command(acceleration_group, name="acceleration")
cli.add_command(seasonality_group, name="seasonality")
cli.add_command(drawdown_group, name="drawdown")
cli.add_command(inflection_group, name="inflection")
cli.add_command(regime_group, name="regime")


# ── top-level commands ──────────────────────────────────────────────────────
@cli.command()
@click.option("--commodity", "-c", default="CORN", show_default=True)
@click.option("--state", "-s", default=None)
@click.option("--year", "-y", default=None, type=int)
@click.option("--simple", is_flag=True, default=False)
@click.option(
    "--export",
    type=click.Choice(["json", "csv"]),
    default=None,
    help="Export format.",
)
@click.option("--out", default=None, help="Output file path for export.")
def progress(
    commodity: str,
    state: str | None,
    year: int | None,
    simple: bool,
    export: str | None,
    out: str | None,
) -> None:
    """Fetch and display crop progress data."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured.", err=True)
        raise SystemExit(1)

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(commodity=commodity, state=state, year=year)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}", err=True)
        raise SystemExit(1)

    if not records:
        click.echo("No data returned.")
        return

    record_query({"commodity": commodity, "state": state, "year": year})

    if export:
        try:
            content = export_data(records, fmt=export)
            write_export(content, path=out)
        except ExportError as exc:
            click.echo(f"Export error: {exc}", err=True)
            raise SystemExit(1)
        return

    if simple:
        click.echo(format_simple_table(records))
    else:
        click.echo(format_crop_progress(records))


@cli.command()
def ping() -> None:
    """Check API connectivity."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: no API key configured.", err=True)
        raise SystemExit(1)
    client = UsdaClient(api_key=api_key)
    try:
        client.get_crop_progress(commodity="CORN")
        click.echo("OK — API reachable.")
    except UsdaClientError as exc:
        click.echo(f"FAIL — {exc}", err=True)
        raise SystemExit(1)


@cli.command(name="history")
@click.option("--limit", default=10, show_default=True, type=int)
def history_cmd(limit: int) -> None:
    """Show recent query history."""
    entries = load_history()[-limit:]
    if not entries:
        click.echo("No history yet.")
        return
    for entry in entries:
        click.echo(entry)


def main() -> None:  # pragma: no cover
    cli()
