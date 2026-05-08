from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_TRAILER = re.compile(r"^Spec:\s*(?P<id>\S+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class CoverageReport:
    total: int
    covered: int
    uncovered_hashes: list[str]

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return 100.0 * self.covered / self.total


def compute_coverage(repo: Path, *, last: int) -> CoverageReport:
    out = subprocess.run(
        ["git", "log", f"-n{last}", "--format=%H%x1f%B%x1e"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if not out:
        return CoverageReport(total=0, covered=0, uncovered_hashes=[])

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
        if _TRAILER.search(body):
            covered += 1
        else:
            uncovered.append(sha)
    return CoverageReport(total=total, covered=covered, uncovered_hashes=uncovered)
