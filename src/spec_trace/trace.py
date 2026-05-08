from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .paths import RepoPaths

_TRAILER = re.compile(r"^Spec:\s*(?P<id>\S+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class TraceResult:
    commit_sha: str
    spec_id: str | None
    spec_text: str
    decisions_text: str


def trace_commit(repo: Path, sha: str) -> TraceResult:
    body = subprocess.run(
        ["git", "log", "-1", "--format=%B", sha],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    match = _TRAILER.search(body)
    if not match:
        return TraceResult(commit_sha=sha, spec_id=None, spec_text="", decisions_text="")
    spec_id = match.group("id")
    paths = RepoPaths(repo)
    spec_file = paths.specs_dir / f"{spec_id}.md"
    log_file = paths.decisions_dir / f"{spec_id}.md"
    return TraceResult(
        commit_sha=sha,
        spec_id=spec_id,
        spec_text=spec_file.read_text(encoding="utf-8") if spec_file.exists() else "",
        decisions_text=log_file.read_text(encoding="utf-8") if log_file.exists() else "",
    )
