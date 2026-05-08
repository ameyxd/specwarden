from pathlib import Path

import pytest
from typer.testing import CliRunner

from spec_trace.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_init_creates_layout(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(app, ["init", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".claude" / "specs").is_dir()
    assert (tmp_path / ".claude" / "decisions").is_dir()


def test_new_then_activate_then_done(runner: CliRunner, tmp_path: Path):
    runner.invoke(app, ["init", "--root", str(tmp_path)])
    r1 = runner.invoke(app, ["new", "Add JWT Auth", "--author", "Amey", "--root", str(tmp_path)])
    assert r1.exit_code == 0, r1.stdout
    spec_id = r1.stdout.strip().split()[-1]

    r2 = runner.invoke(app, ["activate", spec_id, "--root", str(tmp_path)])
    assert r2.exit_code == 0, r2.stdout
    assert (tmp_path / ".claude" / "specs" / "active").read_text().strip() == spec_id

    r3 = runner.invoke(app, ["done", "--root", str(tmp_path)])
    assert r3.exit_code == 0, r3.stdout
    assert not (tmp_path / ".claude" / "specs" / "active").exists()


def test_status_reports_no_active(runner: CliRunner, tmp_path: Path):
    runner.invoke(app, ["init", "--root", str(tmp_path)])
    result = runner.invoke(app, ["status", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "no active spec" in result.stdout.lower()


def test_new_with_empty_title_exits_1(runner: CliRunner, tmp_path: Path):
    runner.invoke(app, ["init", "--root", str(tmp_path)])
    result = runner.invoke(app, ["new", "!!!", "--author", "A", "--root", str(tmp_path)])
    assert result.exit_code == 1


def test_activate_unknown_spec_exits_1(runner: CliRunner, tmp_path: Path):
    runner.invoke(app, ["init", "--root", str(tmp_path)])
    result = runner.invoke(app, ["activate", "2026-05-08_does-not-exist", "--root", str(tmp_path)])
    assert result.exit_code == 1


def test_done_with_no_active_exits_1(runner: CliRunner, tmp_path: Path):
    runner.invoke(app, ["init", "--root", str(tmp_path)])
    result = runner.invoke(app, ["done", "--root", str(tmp_path)])
    assert result.exit_code == 1


def test_trace_no_trailer_exits_1(runner: CliRunner, tmp_path: Path):
    import subprocess

    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "f.txt").write_text("a")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "no trailer"], cwd=tmp_path, check=True)

    result = runner.invoke(app, ["trace", "HEAD", "--root", str(tmp_path)])

    assert result.exit_code == 1


def test_git_hook_install_and_uninstall(runner: CliRunner, tmp_path: Path):
    import subprocess

    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)

    r1 = runner.invoke(app, ["git-hook", "install", "--root", str(tmp_path)])
    assert r1.exit_code == 0, r1.stdout
    hook = tmp_path / ".git" / "hooks" / "prepare-commit-msg"
    assert hook.is_file()

    r2 = runner.invoke(app, ["git-hook", "uninstall", "--root", str(tmp_path)])
    assert r2.exit_code == 0, r2.stdout
    assert not hook.exists()
