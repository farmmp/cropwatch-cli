"""CLI sub-commands for managing crop progress alerts."""

from __future__ import annotations

import click
from cropwatch.alerts import save_alert, load_alerts, clear_alerts, AlertError


@click.group("alerts")
def alerts_group() -> None:
    """Manage threshold-based crop progress alerts."""


@alerts_group.command("add")
@click.argument("commodity")
@click.argument("metric")
@click.argument("threshold", type=float)
@click.option(
    "--condition", "-c",
    type=click.Choice(["above", "below"], case_sensitive=False),
    default="below",
    show_default=True,
    help="Trigger when value is above or below the threshold.",
)
def add_alert(commodity: str, metric: str, threshold: float, condition: str) -> None:
    """Add an alert rule for COMMODITY METRIC at THRESHOLD."""
    try:
        rule = save_alert(commodity.upper(), metric, threshold, condition)
        click.echo(
            f"Alert added: {rule['commodity']} / {rule['metric']} "
            f"{rule['condition']} {rule['threshold']}"
        )
    except AlertError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alerts_group.command("list")
def list_alerts() -> None:
    """List all saved alert rules."""
    rules = load_alerts()
    if not rules:
        click.echo("No alerts configured.")
        return
    click.echo(f"{'#':<4} {'Commodity':<14} {'Metric':<20} {'Cond':<8} {'Threshold'}")
    click.echo("-" * 56)
    for i, r in enumerate(rules, 1):
        click.echo(
            f"{i:<4} {r['commodity']:<14} {r['metric']:<20} "
            f"{r['condition']:<8} {r['threshold']}"
        )


@alerts_group.command("clear")
@click.confirmation_option(prompt="Remove all alerts?")
def clear_alerts_cmd() -> None:
    """Remove all saved alert rules."""
    clear_alerts()
    click.echo("All alerts cleared.")
