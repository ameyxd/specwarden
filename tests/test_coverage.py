import subprocess
from pathlib import Path

import pytest

from spec_trace.coverage import CoverageReport, compute_coverage


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return out.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@t.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "f.txt").write_text("a")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "first commit\n\nSpec: 2026-05-07_demo")
    (tmp_path / "f.txt").write_text("b")
    _git(tmp_path, "commit", "-q", "-am", "second commit, no spec")
    (tmp_path / "f.txt").write_text("c")
    _git(tmp_path, "commit", "-q", "-am", "third commit\n\nSpec: 2026-05-07_demo")
    return tmp_path


def test_compute_coverage_counts_trailers(repo: Path):
    report = compute_coverage(repo, last=10)

    assert isinstance(report, CoverageReport)
    assert report.total == 3
    assert report.covered == 2
    assert len(report.uncovered_hashes) == 1
    assert report.percentage == pytest.approx(2 / 3 * 100, rel=1e-3)


def test_compute_coverage_respects_last(repo: Path):
    report = compute_coverage(repo, last=2)
    assert report.total == 2
