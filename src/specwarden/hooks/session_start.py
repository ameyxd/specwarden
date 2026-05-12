"""specwarden SessionStart hook. Self-contained — stdlib only."""

from __future__ import annotations

import sys
from pathlib import Path

REMINDER = (
    "specwarden: no active spec. Run `/spec <slug>` to define what you're building.\n"
    "  Spec template sections: Assumptions, Scope, Non-goals, Success criteria.\n"
)


def main() -> int:
    repo = Path.cwd()
    marker = repo / ".claude" / "specs" / "active"
    if marker.exists():
        text = marker.read_text(encoding="utf-8").strip()
        if text:
            sys.stdout.write(f"specwarden: active spec is {text}\n")
            return 0
    sys.stdout.write(REMINDER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
