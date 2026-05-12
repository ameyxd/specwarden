from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .trailers import SPEC_TRAILER


@dataclass(frozen=True)
class CoverageReport:
    total: int
    covered: int
    uncovered_hashes: tuple[str, ...]

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return 100.0 * self.covered / self.total


_EMPTY_REPORT = CoverageReport(total=0, covered=0, uncovered_hashes=())


def compute_coverage(repo: Path, *, last: int) -> CoverageReport:
    try:
        result = subprocess.run(
            ["git", "log", f"-n{last}", "--format=%H%x1f%B%x1e"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return _EMPTY_REPORT
    out = result.stdout
    if not out:
        return _EMPTY_REPORT

    records = [r for r in out.split("\x1e") if r.strip()]
    total = 0
    covered = 0
    uncovered: list[str] = []
    for record in records:
        sha, _, body = record.partition("\x1f")
        sha = sha.strip()
        if not sha:
            continue
        total += 1
        if SPEC_TRAILER.search(body):
            covered += 1
        else:
            uncovered.append(sha)
    return CoverageReport(total=total, covered=covered, uncovered_hashes=tuple(uncovered))
