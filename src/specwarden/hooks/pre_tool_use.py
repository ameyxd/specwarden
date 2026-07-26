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

REQUIRED_SECTIONS = ("Assumptions", "Scope", "Non-goals", "Success criteria")

# Placeholder lines the template ships with. A section containing only these has
# not been written, whatever the file's length suggests.
PLACEHOLDERS = {"- todo", "- [ ] todo", "todo"}


def _unfilled_sections(spec_text: str) -> list[str]:
    """Required sections that are absent, empty, or still only template TODOs.

    Without this the gate is satisfied by `specwarden new` plus `activate`: two
    commands and not one word written. The spec is meant to be the forcing
    function, so an untouched template must not unlock editing.
    """
    bodies: dict[str, list[str]] = {}
    current: str | None = None
    for raw in spec_text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            heading = line[3:].strip()
            current = heading if heading in REQUIRED_SECTIONS else None
            if current:
                bodies.setdefault(current, [])
            continue
        if current and line:
            bodies[current].append(line)

    unfilled = []
    for section in REQUIRED_SECTIONS:
        body = bodies.get(section)
        if body is None:
            unfilled.append(section)
            continue
        # The template's explanatory blurb sits directly under the heading, so a
        # section counts as written only if something is neither blurb nor TODO.
        substantive = [
            line
            for line in body
            if line.lstrip("-[] ").strip().lower() not in {"todo", ""}
            and line.strip().lower() not in PLACEHOLDERS
            and (line.startswith(("-", "*", "1.")) or line.startswith("- [ ]"))
        ]
        if not substantive:
            unfilled.append(section)
    return unfilled


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

    spec_path = repo / ".claude" / "specs" / f"{spec_id}.md"
    if not spec_path.exists():
        print(
            _decision(
                "deny",
                f"specwarden: active spec is {spec_id} but {spec_path} does not exist. "
                "Run `/spec <slug>` to create it.",
            )
        )
        return 0

    unfilled = _unfilled_sections(spec_path.read_text(encoding="utf-8"))
    if unfilled:
        print(
            _decision(
                "deny",
                f"specwarden: spec {spec_id} still has unwritten sections: "
                f"{', '.join(unfilled)}. Fill them in before editing files. "
                "An empty template is not a spec.",
            )
        )
        return 0

    print(_decision("allow", f"specwarden: active spec is {spec_id}."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
