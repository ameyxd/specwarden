import stat
import subprocess
from pathlib import Path

import pytest

from specwarden.git_hook import install_hook, uninstall_hook


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@t.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    return tmp_path


def test_install_creates_executable_hook(repo: Path):
    install_hook(repo)
    hook = repo / ".git" / "hooks" / "prepare-commit-msg"
    assert hook.is_file()
    assert hook.stat().st_mode & stat.S_IXUSR


def test_hook_appends_trailer_when_active(repo: Path):
    install_hook(repo)
    (repo / ".claude" / "specs" / "active").write_text("2026-05-07_demo\n")

    (repo / "f.txt").write_text("hi")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "do thing")

    body = _git(repo, "log", "-1", "--format=%B")
    assert "Spec: 2026-05-07_demo" in body


def test_hook_is_noop_when_no_active(repo: Path):
    install_hook(repo)
    (repo / "f.txt").write_text("hi")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "do thing")
    body = _git(repo, "log", "-1", "--format=%B")
    assert "Spec:" not in body


def test_uninstall_removes_managed_hook(repo: Path):
    install_hook(repo)
    uninstall_hook(repo)
    assert not (repo / ".git" / "hooks" / "prepare-commit-msg").exists()


def test_uninstall_preserves_unmanaged_hook(repo: Path):
    hook = repo / ".git" / "hooks" / "prepare-commit-msg"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho hand-written\n")
    hook.chmod(0o755)

    uninstall_hook(repo)

    assert hook.exists()
    assert "hand-written" in hook.read_text()


def test_install_refuses_unmanaged_hook(repo: Path):
    hook = repo / ".git" / "hooks" / "prepare-commit-msg"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho hand-written\n")

    with pytest.raises(RuntimeError, match="already exists"):
        install_hook(repo)


def test_install_is_idempotent_on_managed_hook(repo: Path):
    install_hook(repo)
    install_hook(repo)
    hook = repo / ".git" / "hooks" / "prepare-commit-msg"
    text = hook.read_text()
    assert text.count("# managed-by: specwarden") == 1


def test_install_rejects_non_git_repo(tmp_path: Path):
    with pytest.raises(RuntimeError, match=".git"):
        install_hook(tmp_path)


def test_hook_skips_double_trailer(repo: Path):
    install_hook(repo)
    (repo / ".claude" / "specs" / "active").write_text("2026-05-07_demo\n")

    (repo / "f.txt").write_text("hi")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "do thing\n\nSpec: 2026-05-07_demo")

    body = _git(repo, "log", "-1", "--format=%B")
    assert body.count("Spec: 2026-05-07_demo") == 1
