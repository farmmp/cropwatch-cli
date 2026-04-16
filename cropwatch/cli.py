import click
import os
from cropwatch.usda_client import UsdaClient, UsdaClientError
from cropwatch.formatter import format_crop_progress, format_simple_table


@click.group()
def cli():
    """CropWatch CLI — fetch and visualize USDA crop progress reports."""
    pass


@cli.command()
@click.argument("commodity")
@click.option("--state", "-s", default=None, help="State abbreviation (e.g. IA, IL).")
@click.option("--year", "-y", default=None, type=int, help="Year (e.g. 2023).")
@click.option("--simple", is_flag=True, default=False, help="Show simple table without progress bars.")
@click.option("--api-key", envvar="USDA_API_KEY", default=None, help="USDA NASS API key.")
def progress(commodity, state, year, simple, api_key):
    """Fetch crop progress for a given COMMODITY."""
    try:
        client = UsdaClient(api_key=api_key)
        data = client.get_crop_progress(commodity=commodity, state=state, year=year)
    except UsdaClientError as e:
        raise click.ClickException(str(e))

    if not data:
        click.echo("No data found for the given parameters.")
        return

    if simple:
        output = format_simple_table(data)
    else:
        output = format_crop_progress(data, commodity=commodity, state=state)

    click.echo(output)


@cli.command()
@click.option("--api-key", envvar="USDA_API_KEY", default=None, help="USDA NASS API key.")
def ping(api_key):
    """Verify connectivity and API key validity."""
    try:
        client = UsdaClient(api_key=api_key)
        data = client.get_crop_progress(commodity="CORN", year=2023)
        if data:
            click.echo(click.style("✓ Connection successful.", fg="green"))
        else:
            click.echo(click.style("⚠ Connected but received empty response.", fg="yellow"))
    except UsdaClientError as e:
        raise click.ClickException(str(e))


def main():
    cli()


if __name__ == "__main__":
    main()
