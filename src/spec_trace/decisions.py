from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from .paths import RepoPaths


@dataclass(frozen=True)
class DecisionEntry:
    file_path: str
    line_range: str
    summary: str
    tool: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def append_decision(
    paths: RepoPaths,
    spec_id: str,
    entry: DecisionEntry,
    *,
    now: Callable[[], datetime] = _now,
) -> None:
    paths.ensure_dirs()
    log = paths.decisions_dir / f"{spec_id}.md"
    block = (
        f"## {now().isoformat(timespec='seconds')}\n"
        f"- File: {entry.file_path}\n"
        f"- Lines: {entry.line_range}\n"
        f"- Summary: {entry.summary}\n"
        f"- Tool: {entry.tool}\n\n"
    )
    with log.open("a", encoding="utf-8") as f:
        if f.tell() == 0:
            f.write(
                f"# Decisions: {spec_id}\n\nAppend-only log of changes authorized by this spec.\n\n"
            )
        f.write(block)
