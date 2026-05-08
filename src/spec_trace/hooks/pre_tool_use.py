"""spec-trace PreToolUse hook. Self-contained — no internal imports."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

EDITING_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def _active_spec_id(repo: Path) -> str | None:
    marker = repo / ".claude" / "specs" / "active"
    if not marker.exists():
        return None
    text = marker.read_text(encoding="utf-8").strip()
    return text or None


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    tool = payload.get("tool_name", "")
    if tool not in EDITING_TOOLS:
        print(json.dumps({"permissionDecision": "allow"}))
        return 0

    if os.environ.get("SPEC_TRACE_QUICKFIX") == "1":
        print(json.dumps({"permissionDecision": "allow"}))
        return 0

    repo = Path.cwd()
    if _active_spec_id(repo) is None:
        print(
            json.dumps(
                {
                    "permissionDecision": "ask",
                    "message": (
                        "spec-trace: no active spec. Run `/spec <slug>` first to define "
                        "what you're building before editing files."
                    ),
                }
            )
        )
        return 0

    print(json.dumps({"permissionDecision": "allow"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
