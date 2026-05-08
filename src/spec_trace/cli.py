from __future__ import annotations

import json
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

SETTINGS_TEMPLATE = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Edit|Write|MultiEdit|NotebookEdit",
                "hooks": [
                    {"type": "command", "command": "python -m spec_trace.hooks.pre_tool_use"}
                ],
            }
        ],
        "PostToolUse": [
            {
                "matcher": "Edit|Write|MultiEdit|NotebookEdit",
                "hooks": [
                    {"type": "command", "command": "python -m spec_trace.hooks.post_tool_use"}
                ],
            }
        ],
        "SessionStart": [
            {"hooks": [{"type": "command", "command": "python -m spec_trace.hooks.session_start"}]}
        ],
    }
}

app = typer.Typer(add_completion=False, help="spec-trace: spec-first discipline, with teeth.")

ROOT_OPTION = typer.Option(None, "--root", help="Repo root (defaults to current directory).")


def _resolve_root(root: Path | None) -> Path:
    return root if root is not None else Path.cwd()


@app.command()
def init(root: Path | None = ROOT_OPTION) -> None:
    """Create the .claude/ layout and a default settings.json wiring the hooks."""
    paths = RepoPaths(_resolve_root(root))
    paths.ensure_dirs()
    settings_path = paths.claude_dir / "settings.json"
    if not settings_path.exists():
        settings_path.write_text(json.dumps(SETTINGS_TEMPLATE, indent=2) + "\n", encoding="utf-8")
        typer.echo(f"initialized: {paths.claude_dir} (wrote settings.json)")
    else:
        typer.echo(f"initialized: {paths.claude_dir} (settings.json already exists; left alone)")


@app.command("new")
def new_cmd(
    title: str,
    author: str = typer.Option(..., "--author", "-a"),
    root: Path | None = ROOT_OPTION,
) -> None:
    """Create a new spec from the four-section template."""
    paths = RepoPaths(_resolve_root(root))
    try:
        spec_id = create_spec(paths, title, author=author)
    except SpecError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"created spec {spec_id}")


@app.command()
def activate(spec_id: str, root: Path | None = ROOT_OPTION) -> None:
    """Mark a spec as the active one — subsequent edits get logged here."""
    paths = RepoPaths(_resolve_root(root))
    try:
        activate_spec(paths, spec_id)
    except SpecError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"active: {spec_id}")


@app.command()
def done(root: Path | None = ROOT_OPTION) -> None:
    """Mark the active spec as completed and clear the marker."""
    paths = RepoPaths(_resolve_root(root))
    try:
        spec_id = mark_done(paths)
    except SpecError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"completed: {spec_id}")


@app.command()
def status(root: Path | None = ROOT_OPTION) -> None:
    """Print the active spec, if any."""
    paths = RepoPaths(_resolve_root(root))
    spec_id = paths.active_spec_id()
    if spec_id is None:
        typer.echo("no active spec — run `spec-trace new <title>` to start.")
        return
    typer.echo(f"active: {spec_id}")


@app.command()
def coverage(
    last: int = typer.Option(50, "--last", "-n"),
    root: Path | None = ROOT_OPTION,
) -> None:
    """Report Spec: trailer coverage over the last N commits."""
    report = compute_coverage(_resolve_root(root), last=last)
    typer.echo(
        f"{report.covered}/{report.total} commits have spec coverage ({report.percentage:.0f}%)"
    )
    if report.uncovered_hashes:
        typer.echo("uncovered:")
        for sha in report.uncovered_hashes:
            typer.echo(f"  {sha[:12]}")


@app.command()
def trace(
    commit: str = typer.Argument("HEAD"),
    root: Path | None = ROOT_OPTION,
) -> None:
    """Print the full chain (commit -> spec -> decisions)."""
    result = trace_commit(_resolve_root(root), commit)
    typer.echo(f"commit: {result.commit_sha}")
    if result.spec_id is None:
        typer.echo("no Spec: trailer on this commit.", err=True)
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


git_hook_app = typer.Typer(help="Manage the prepare-commit-msg git hook.")
app.add_typer(git_hook_app, name="git-hook")


@git_hook_app.command("install")
def git_hook_install(root: Path | None = ROOT_OPTION) -> None:
    """Install the prepare-commit-msg hook."""
    from .git_hook import install_hook

    path = install_hook(_resolve_root(root))
    typer.echo(f"installed: {path}")


@git_hook_app.command("uninstall")
def git_hook_uninstall(root: Path | None = ROOT_OPTION) -> None:
    """Uninstall the prepare-commit-msg hook (if installed by spec-trace)."""
    from .git_hook import uninstall_hook

    uninstall_hook(_resolve_root(root))
    typer.echo("uninstalled.")
