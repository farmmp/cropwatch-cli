"""CLI command group for baseline comparison."""
import click
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.config import get_api_key
from cropwatch.baseline import compute_baseline, format_baseline, BaselineError


@click.group("baseline")
def baseline_group():
    """Compare current crop progress against historical baseline."""


@baseline_group.command("compare")
@click.option("--commodity", "-c", required=True, help="Crop commodity (e.g. CORN).")
@click.option("--week", "-w", required=True, help="Week ending date (YYYY-MM-DD).")
@click.option("--year", "-y", required=True, type=int, help="Current year to compare.")
@click.option("--state", "-s", default=None, help="State abbreviation (optional).")
@click.option("--years-back", default=5, show_default=True, help="How many prior years to fetch.")
def compare(commodity: str, week: str, year: int, state: str | None, years_back: int):
    """Show how current year stacks up against the historical average."""
    api_key = get_api_key()
    if not api_key:
        click.echo("Error: No API key configured. Set USDA_API_KEY or run 'cropwatch config'.")
        raise SystemExit(1)

    all_records: list[dict] = []
    client = UsdaClient(api_key)
    fetch_years = list(range(year - years_back, year + 1))

    try:
        for y in fetch_years:
            records = client.get_crop_progress(commodity=commodity, year=y, state=state)
            all_records.extend(records)
    except UsdaClientError as exc:
        click.echo(f"API error: {exc}")
        raise SystemExit(1)

    try:
        result = compute_baseline(all_records, commodity=commodity, week_ending=week, current_year=year)
    except BaselineError as exc:
        click.echo(f"Baseline error: {exc}")
        raise SystemExit(1)

    click.echo(format_baseline(result))
