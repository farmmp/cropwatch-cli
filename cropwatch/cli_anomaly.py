"""CLI commands for anomaly detection."""
import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.anomaly import detect_anomalies, format_anomalies, AnomalyError


@click.group("anomaly")
def anomaly_group():
    """Detect anomalies in crop progress data."""


@anomaly_group.command("scan")
@click.option("--crop", default="corn", show_default=True, help="Crop name.")
@click.option("--state", default=None, help="State abbreviation (optional).")
@click.option("--year", default=2023, show_default=True, type=int, help="Year to scan.")
@click.option("--key", default="value", show_default=True, help="Data key to check.")
@click.option("--threshold", default=1.5, show_default=True, type=float,
              help="Std-dev threshold for anomaly.")
def scan(crop, state, year, key, threshold):
    """Scan a year of crop progress for statistical anomalies."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: No API key configured. Set USDA_API_KEY or run `cropwatch config set-key`.", err=True)
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
    try:
        anomalies = detect_anomalies(records, key, threshold=threshold)
    except AnomalyError as exc:
        click.echo(f"Anomaly error: {exc}", err=True)
        raise SystemExit(1)
    click.echo(f"Anomaly scan — {crop.title()} {year}" + (f" [{state}]" if state else ""))
    click.echo(format_anomalies(anomalies, key))
