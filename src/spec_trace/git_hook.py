from __future__ import annotations

import stat
from pathlib import Path

# `\\n` in the printf line is intentional: Python writes a literal `\n` to disk,
# which bash printf then interprets as a real newline. Do not "fix" to `\n`.
# `grep -qxF` does whole-line fixed-string matching — robust against any
# regex metacharacters that might appear in future spec ID formats.
HOOK_SCRIPT = """\
#!/usr/bin/env bash
# managed-by: spec-trace
set -e
COMMIT_MSG_FILE="$1"
ACTIVE_FILE="$(git rev-parse --show-toplevel)/.claude/specs/active"
if [ -f "$ACTIVE_FILE" ]; then
    SPEC_ID="$(tr -d '[:space:]' < "$ACTIVE_FILE")"
    if [ -n "$SPEC_ID" ] && ! grep -qxF "Spec: $SPEC_ID" "$COMMIT_MSG_FILE"; then
        printf "\\nSpec: %s\\n" "$SPEC_ID" >> "$COMMIT_MSG_FILE"
    fi
fi
"""

MANAGED_MARKER = "# managed-by: spec-trace"


def _hook_path(repo: Path) -> Path:
    return repo / ".git" / "hooks" / "prepare-commit-msg"


def install_hook(repo: Path) -> Path:
    if not (repo / ".git").is_dir():
        raise RuntimeError(f"{repo} does not contain a .git directory.")
    path = _hook_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and MANAGED_MARKER not in path.read_text(encoding="utf-8"):
        raise RuntimeError(
            "prepare-commit-msg hook already exists and was not installed by spec-trace; "
            "remove it manually or merge by hand."
        )
    path.write_text(HOOK_SCRIPT, encoding="utf-8")
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def uninstall_hook(repo: Path) -> None:
    path = _hook_path(repo)
    if not path.exists():
        return
    if MANAGED_MARKER in path.read_text(encoding="utf-8"):
        path.unlink()
