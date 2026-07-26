"""specwarden PostToolUse hook. Self-contained — stdlib only."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EDITING_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def _active_spec_id(repo: Path) -> str | None:
    marker = repo / ".claude" / "specs" / "active"
    if not marker.exists():
        return None
    text = marker.read_text(encoding="utf-8").strip()
    return text or None


def _relative_to_repo(file_path: str, repo: Path) -> str:
    """Record repo-relative paths.

    Claude Code passes an absolute `file_path`. Writing it verbatim puts the
    operator's machine layout into a file that is meant to be committed and read
    by someone else six months later, and makes the log differ between two
    checkouts of the same repo. Paths outside the repo stay absolute, since
    there is nothing sensible to make them relative to.
    """
    if not file_path or file_path == "<unknown>":
        return "<unknown>"
    try:
        return Path(file_path).resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return file_path


def _summary(payload: dict, repo: Path) -> tuple[str, str]:
    inp = payload.get("tool_input", {}) or {}
    file_path = _relative_to_repo(inp.get("file_path", "<unknown>"), repo)
    if "old_string" in inp:
        line_range = "edit"
    elif "content" in inp:
        lines = inp.get("content", "").count("\n") + 1
        line_range = f"1-{lines} (created)"
    else:
        line_range = "edit"
    return file_path, line_range


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    tool = payload.get("tool_name", "")
    if tool not in EDITING_TOOLS:
        return 0

    repo = Path.cwd()
    spec_id = _active_spec_id(repo)
    if spec_id is None:
        return 0

    file_path, line_range = _summary(payload, repo)
    log_dir = repo / ".claude" / "decisions"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{spec_id}.md"
    block = (
        f"## {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"- File: {file_path}\n"
        f"- Lines: {line_range}\n"
        f"- Summary: {tool} on {file_path}\n"
        f"- Tool: {tool}\n\n"
    )
    with log_file.open("a", encoding="utf-8") as f:
        if f.tell() == 0:
            f.write(
                f"# Decisions: {spec_id}\n\nAppend-only log of changes authorized by this spec.\n\n"
            )
        f.write(block)
    return 0


if __name__ == "__main__":
    sys.exit(main())
