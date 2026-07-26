"""specwarden PreToolUse hook. Self-contained — no internal imports."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

EDITING_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

NO_SPEC_MESSAGE = (
    "specwarden: no active spec. Run `/spec <slug>` first to define "
    "what you're building before editing files."
)


def _decision(decision: str, reason: str = "") -> str:
    """Serialise a PreToolUse decision in the shape Claude Code actually reads.

    Claude Code takes the decision from `hookSpecificOutput.permissionDecision`;
    a bare top-level `permissionDecision` is ignored, which silently disables the
    gate. On a deny we also emit the legacy top-level `decision`/`reason` pair,
    which older hosts honour and current ones still accept.
    """
    payload: dict[str, object] = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }
    if decision == "deny":
        payload["decision"] = "block"
        payload["reason"] = reason
    return json.dumps(payload)


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
        print(_decision("allow", "specwarden: not an editing tool."))
        return 0

    if os.environ.get("SPECWARDEN_QUICKFIX") == "1":
        print(_decision("allow", "specwarden: SPECWARDEN_QUICKFIX=1 set."))
        return 0

    repo = Path.cwd()
    spec_id = _active_spec_id(repo)
    if spec_id is None:
        print(_decision("deny", NO_SPEC_MESSAGE))
        return 0

    print(_decision("allow", f"specwarden: active spec is {spec_id}."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
