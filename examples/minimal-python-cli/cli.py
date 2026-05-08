"""Date CLI — prints the current date/time in various formats."""
from __future__ import annotations

import click
from datetime import datetime, timezone


@click.group()
def cli() -> None:
    """Utility commands for working with dates and times."""


@cli.command()
@click.option("--fmt", default="%Y-%m-%d %H:%M:%S", show_default=True, help="strftime format string.")
@click.option("--utc", is_flag=True, default=False, help="Print UTC time instead of local time.")
def now(fmt: str, utc: bool) -> None:
    """Print the current date and time."""
    if utc:
        ts = datetime.now(timezone.utc)
    else:
        ts = datetime.now()
    click.echo(ts.strftime(fmt))


@cli.command()
@click.argument("date_str")
def parse(date_str: str) -> None:
    """Parse a date string and print it in ISO-8601."""
    try:
        parsed = datetime.fromisoformat(date_str)
    except ValueError as exc:
        raise click.BadParameter(str(exc), param_hint="DATE_STR") from exc
    click.echo(parsed.isoformat())


if __name__ == "__main__":
    cli()
