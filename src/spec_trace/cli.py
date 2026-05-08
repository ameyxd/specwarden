from __future__ import annotations

from pathlib import Path

import typer

from . import __version__
from .coverage import compute_coverage
from .paths import RepoPaths
from .spec import (
    SpecError,
    activate_spec,
    create_spec,
    mark_done,
)
from .trace import trace_commit

app = typer.Typer(add_completion=False, help="spec-trace: spec-first discipline, with teeth.")


def _root_option() -> Path:
    return typer.Option(Path.cwd(), "--root", help="Repo root.")


@app.command()
def init(root: Path = _root_option()) -> None:
    """Create the .claude/ layout in the current repo."""
    paths = RepoPaths(root)
    paths.ensure_dirs()
    typer.echo(f"initialized: {paths.claude_dir}")


@app.command("new")
def new_cmd(
    title: str,
    author: str = typer.Option(..., "--author", "-a"),
    root: Path = _root_option(),
) -> None:
    """Create a new spec from the four-section template."""
    paths = RepoPaths(root)
    try:
        spec_id = create_spec(paths, title, author=author)
    except SpecError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"created spec {spec_id}")


@app.command()
def activate(spec_id: str, root: Path = _root_option()) -> None:
    """Mark a spec as the active one — subsequent edits get logged here."""
    paths = RepoPaths(root)
    try:
        activate_spec(paths, spec_id)
    except SpecError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"active: {spec_id}")


@app.command()
def done(root: Path = _root_option()) -> None:
    """Mark the active spec as completed and clear the marker."""
    paths = RepoPaths(root)
    try:
        spec_id = mark_done(paths)
    except SpecError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"completed: {spec_id}")


@app.command()
def status(root: Path = _root_option()) -> None:
    """Print the active spec, if any."""
    paths = RepoPaths(root)
    spec_id = paths.active_spec_id()
    if spec_id is None:
        typer.echo("no active spec — run `spec-trace new <title>` to start.")
        return
    typer.echo(f"active: {spec_id}")


@app.command()
def coverage(
    last: int = typer.Option(50, "--last", "-n"),
    root: Path = _root_option(),
) -> None:
    """Report Spec: trailer coverage over the last N commits."""
    report = compute_coverage(root, last=last)
    typer.echo(
        f"{report.covered}/{report.total} commits have spec coverage ({report.percentage:.0f}%)"
    )
    if report.uncovered_hashes:
        typer.echo("uncovered:")
        for sha in report.uncovered_hashes:
            typer.echo(f"  {sha[:12]}")


@app.command()
def trace(commit: str = typer.Argument("HEAD"), root: Path = _root_option()) -> None:
    """Print the full chain (commit -> spec -> decisions)."""
    result = trace_commit(root, commit)
    typer.echo(f"commit: {result.commit_sha}")
    if result.spec_id is None:
        typer.echo("no Spec: trailer on this commit.")
        raise typer.Exit(code=1)
    typer.echo(f"spec:   {result.spec_id}")
    typer.echo("---")
    typer.echo(result.spec_text)
    typer.echo("---")
    typer.echo(result.decisions_text)


@app.command()
def version() -> None:
    """Print the installed version."""
    typer.echo(__version__)
