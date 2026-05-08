import subprocess
from pathlib import Path

import pytest

from spec_trace.trace import TraceResult, trace_commit


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
    (tmp_path / ".claude" / "specs" / "2026-05-07_demo.md").write_text("# spec body")
    (tmp_path / ".claude" / "decisions").mkdir()
    (tmp_path / ".claude" / "decisions" / "2026-05-07_demo.md").write_text("# log body")
    (tmp_path / "f.txt").write_text("a")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "covered commit\n\nSpec: 2026-05-07_demo")
    return tmp_path


def test_trace_returns_chain(repo: Path):
    sha = _git(repo, "rev-parse", "HEAD").strip()

    result = trace_commit(repo, sha)

    assert isinstance(result, TraceResult)
    assert result.commit_sha == sha
    assert result.spec_id == "2026-05-07_demo"
    assert "spec body" in result.spec_text
    assert "log body" in result.decisions_text


def test_trace_returns_none_when_no_trailer(repo: Path):
    (repo / "f.txt").write_text("b")
    _git(repo, "commit", "-q", "-am", "no trailer")
    sha = _git(repo, "rev-parse", "HEAD").strip()

    result = trace_commit(repo, sha)

    assert result.spec_id is None
    assert result.spec_text == ""
    assert result.decisions_text == ""
