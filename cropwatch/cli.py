"""Entry-point for the cropwatch CLI."""

from __future__ import annotations

import click

from cropwatch.cli_alerts import alerts_group
from cropwatch.cli_anomaly import anomaly_group
from cropwatch.cli_baseline import baseline_group
from cropwatch.cli_compare import compare_group
from cropwatch.cli_correlation import correlation_group
from cropwatch.cli_forecast import forecast_group
from cropwatch.cli_heatmap import heatmap_group
from cropwatch.cli_momentum import momentum_group
from cropwatch.cli_moving_avg import movavg_group
from cropwatch.cli_percentile import percentile_group
from cropwatch.cli_plateau import plateau_group
from cropwatch.cli_rebound import rebound_group
from cropwatch.cli_saturation import saturation_group
from cropwatch.cli_seasonavg import seasonavg_group
from cropwatch.cli_smooth import smooth_group
from cropwatch.cli_streak import streak_group
from cropwatch.cli_trend import trend_group
from cropwatch.cli_volatility import volatility_group
from cropwatch.config import get_api_key, save_config
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.formatter import format_crop_progress, format_simple_table
from cropwatch.history import load_history, record_query
from cropwatch.cache import clear_cache
from cropwatch.export import export_data, write_export, ExportError


@click.group()
def cli() -> None:
    """CropWatch — USDA crop progress in your terminal."""


# ── inline commands ────────────────────────────────────────────────────────

@cli.command()
@click.option("--commodity", "-c", default="CORN", show_default=True)
@click.option("--state", "-s", default=None)
@click.option("--year", "-y", default=None, type=int)
@click.option("--simple", is_flag=True, default=False)
@click.option(
    "--export",
    "export_fmt",
    type=click.Choice(["json", "csv"], case_sensitive=False),
    default=None,
)
@click.option("--output", "-o", default=None, type=click.Path())
def progress(
    commodity: str,
    state: str | None,
    year: int | None,
    simple: bool,
    export_fmt: str | None,
    output: str | None,
) -> None:
    """Fetch and display the latest crop progress report."""
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException("No API key configured.")

    client = UsdaClient(api_key=api_key)
    try:
        records = client.get_crop_progress(commodity=commodity, year=year, state=state)
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc

    if not records:
        click.echo("No data returned.")
        return

    record_query(commodity=commodity, state=state, year=year)

    if export_fmt:
        try:
            content = export_data(records, fmt=export_fmt)
            write_export(content, path=output)
        except ExportError as exc:
            raise click.ClickException(str(exc)) from exc
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
        raise click.ClickException("No API key configured.")
    client = UsdaClient(api_key=api_key)
    try:
        client.get_crop_progress(commodity="CORN")
        click.echo("OK — USDA NASS API is reachable.")
    except UsdaClientError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("history")
@click.option("--limit", default=10, show_default=True, type=int)
def history_cmd(limit: int) -> None:
    """Show recent query history."""
    entries = load_history()[:limit]
    if not entries:
        click.echo("No history yet.")
        return
    for e in entries:
        parts = [e.get("commodity", "?")]
        if e.get("state"):
            parts.append(e["state"])
        if e.get("year"):
            parts.append(str(e["year"]))
        click.echo(f"{e.get('timestamp', '?')}  {' / '.join(parts)}")


# ── sub-command groups ─────────────────────────────────────────────────────

cli.add_command(alerts_group)
cli.add_command(anomaly_group)
cli.add_command(baseline_group)
cli.add_command(compare_group)
cli.add_command(correlation_group)
cli.add_command(forecast_group)
cli.add_command(heatmap_group)
cli.add_command(momentum_group)
cli.add_command(movavg_group)
cli.add_command(percentile_group)
cli.add_command(plateau_group)
cli.add_command(rebound_group)
cli.add_command(saturation_group)
cli.add_command(seasonavg_group)
cli.add_command(smooth_group)
cli.add_command(streak_group)
cli.add_command(trend_group)
cli.add_command(volatility_group)


def main() -> None:  # pragma: no cover
    cli()
