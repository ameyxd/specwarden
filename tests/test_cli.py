import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specwarden.cli import app


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


def test_init_writes_settings_with_hooks(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(app, ["init", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.stdout

    settings_path = tmp_path / ".claude" / "settings.json"
    assert settings_path.exists()

    import json

    settings = json.loads(settings_path.read_text())
    assert "PreToolUse" in settings["hooks"]
    assert "PostToolUse" in settings["hooks"]
    assert "SessionStart" in settings["hooks"]

    pre = settings["hooks"]["PreToolUse"][0]
    assert pre["matcher"] == "Edit|Write|MultiEdit|NotebookEdit"
    assert pre["hooks"][0]["command"].endswith("-m specwarden.hooks.pre_tool_use")


def test_init_writes_a_resolvable_interpreter_path(runner: CliRunner, tmp_path: Path):
    """A bare `python` is absent on stock macOS and cannot import a pipx install."""
    import json
    import shlex

    runner.invoke(app, ["init", "--root", str(tmp_path)])
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    interpreter = shlex.split(settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"])[0]
    assert Path(interpreter).is_absolute()


def test_init_hook_command_actually_runs(runner: CliRunner, tmp_path: Path):
    """End-to-end: the command `init` writes must execute and emit a decision."""
    import json
    import subprocess

    runner.invoke(app, ["init", "--root", str(tmp_path)])
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    proc = subprocess.run(
        command,
        shell=True,
        input=json.dumps({"tool_name": "Edit"}),
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_init_preserves_existing_settings(runner: CliRunner, tmp_path: Path):
    (tmp_path / ".claude").mkdir()
    existing = '{"existing": "value"}'
    (tmp_path / ".claude" / "settings.json").write_text(existing)

    result = runner.invoke(app, ["init", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.stdout

    # init should not clobber an existing settings file
    assert (tmp_path / ".claude" / "settings.json").read_text() == existing


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


def test_coverage_reports_against_real_commits(runner: CliRunner, tmp_path: Path):
    import subprocess

    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "f.txt").write_text("a")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "covered\n\nSpec: 2026-05-28_demo"],
        cwd=tmp_path,
        check=True,
    )
    (tmp_path / "f.txt").write_text("b")
    subprocess.run(
        ["git", "commit", "-q", "-am", "uncovered, no trailer"], cwd=tmp_path, check=True
    )

    result = runner.invoke(app, ["coverage", "--last", "10", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.stdout
    assert "1/2 commits have spec coverage (50%)" in result.stdout
    assert "uncovered:" in result.stdout


def test_trace_with_active_spec_succeeds(runner: CliRunner, tmp_path: Path):
    import subprocess

    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)

    assert runner.invoke(app, ["init", "--root", str(tmp_path)]).exit_code == 0
    r_new = runner.invoke(app, ["new", "demo trace spec", "--author", "t", "--root", str(tmp_path)])
    assert r_new.exit_code == 0, r_new.stdout
    spec_id = r_new.stdout.strip().split()[-1]
    assert runner.invoke(app, ["activate", spec_id, "--root", str(tmp_path)]).exit_code == 0

    (tmp_path / ".claude" / "decisions" / f"{spec_id}.md").write_text(
        f"# Decisions: {spec_id}\n\nlog body\n"
    )
    (tmp_path / "f.txt").write_text("a")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", f"feat: demo\n\nSpec: {spec_id}"],
        cwd=tmp_path,
        check=True,
    )

    result = runner.invoke(app, ["trace", "HEAD", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.stdout
    assert "commit:" in result.stdout
    assert f"spec:   {spec_id}" in result.stdout
    assert "demo trace spec" in result.stdout
    assert "log body" in result.stdout
