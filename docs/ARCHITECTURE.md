# Architecture

specwarden has three pieces: a CLI, a set of hooks, and a skill. Each piece does one job. This document describes what each piece is, how they connect, and the data flow for each operation.

## Three pieces

**The CLI (`specwarden`)** is the user-facing command-line tool. It creates specs, activates them, marks them complete, reports coverage, and traces commits back to their originating spec. It also installs the git hook that appends `Spec:` trailers to commit messages. Installed via `pipx install specwarden`; entry point is `specwarden`.

**The hooks** are three Python scripts invoked by Claude Code's lifecycle events. They run as child processes: Claude Code serializes a JSON payload to stdin, the hook reads it, writes a JSON response to stdout, and exits. The hooks live under `src/specwarden/hooks/` and ship inside the Python wheel; `specwarden init` records the absolute path of each script so it runs regardless of how the package was installed. See `docs/HOOKS.md` for the full JSON contract.

**The skill (`SKILL.md`)** is the natural-language description loaded into the model's context. It defines four slash commands (`/spec`, `/trace`, `/coverage`, `/spec-help`) and explains the spec-first discipline. It shapes model behavior before any hook fires. The skill lives at `.claude/skills/specwarden/SKILL.md` and is loaded by Claude Code at session start.

The three pieces are layered: the skill provides advisory guidance, the hooks enforce mechanically, the CLI manages state. Removing the skill degrades the model's awareness of the workflow. Removing the hooks removes enforcement but leaves advisory guidance intact. Removing the CLI leaves the hooks functional (they read files directly) but makes spec management manual.

## The `.claude/` layout in a user repo

After `specwarden init` runs in a repository, the layout is:

```
<user-repo>/
├── .claude/
│   ├── settings.json          # Hook wiring; written once by `specwarden init`
│   ├── specs/
│   │   ├── active             # Single line: the spec ID currently active (or absent)
│   │   ├── 2026-05-06_add-jwt-auth.md
│   │   ├── 2026-05-06_refactor-logger.md
│   │   └── ...
│   └── decisions/
│       ├── 2026-05-06_add-jwt-auth.md   # Append-only log per spec
│       └── ...
└── (the rest of the repo)
```

The `.claude/specs/active` file is the synchronization point between all three pieces. When it exists and contains a non-empty spec ID, edits are allowed and logged. When it is absent or empty, the PreToolUse hook blocks edits. The file is a single line with no trailing whitespace and no BOM; the CLI and hooks both strip whitespace when reading it.

## The `RepoPaths` abstraction

The `src/specwarden/paths.py` module defines `RepoPaths`, which resolves all paths relative to a given repo root. Every CLI command and the hooks all derive paths through this abstraction:

```
repo_root/
  .claude/              → paths.claude_dir
  .claude/specs/        → paths.specs_dir
  .claude/specs/active  → paths.active_marker
  .claude/decisions/    → paths.decisions_dir
```

`RepoPaths.active_spec_id()` reads the active marker and returns `None` if it is absent or empty. The hooks each contain an inlined `_active_spec_id()` function (no internal imports) to keep them self-contained and avoid import failures from breaking hook invocations.

## Data flow per CLI command

### `specwarden init`

```
specwarden init
    └─ RepoPaths.ensure_dirs()
          creates .claude/specs/ and .claude/decisions/ if absent
    └─ writes .claude/settings.json (if not present)
          contains hook wiring for PreToolUse, PostToolUse, SessionStart
    → prints "initialized: .claude/ (wrote settings.json)"
       or "initialized: .claude/ (settings.json already exists; left alone)"
```

`init` will not overwrite an existing `settings.json`. If one exists, it prints a message and exits without modification. Merge by hand if you need to add specwarden hooks to an existing settings file.

### `specwarden new <title> --author <name>`

```
specwarden new "add jwt auth" --author "alice"
    └─ slugify("add jwt auth")          → "add-jwt-auth"
    └─ spec_id = "2026-05-06_add-jwt-auth"
    └─ writes .claude/specs/2026-05-06_add-jwt-auth.md  (from SPEC_TEMPLATE)
    → prints "created spec 2026-05-06_add-jwt-auth"
```

Fails with an error if the slug produces an existing file (same title on the same day). The spec file is not automatically activated; run `specwarden activate` next.

### `specwarden activate <spec-id>`

```
specwarden activate 2026-05-06_add-jwt-auth
    └─ verifies .claude/specs/2026-05-06_add-jwt-auth.md exists
    └─ writes "2026-05-06_add-jwt-auth\n" to .claude/specs/active
    → prints "active: 2026-05-06_add-jwt-auth"
```

Subsequent PreToolUse hook invocations will read this file and allow edits.

### `specwarden done`

```
specwarden done
    └─ reads .claude/specs/active → spec_id
    └─ reads .claude/specs/<spec-id>.md
    └─ replaces "**Status:** active" with "**Status:** completed"
    └─ unlinks .claude/specs/active
    → prints "completed: <spec-id>"
```

### `specwarden coverage --last N`

```
specwarden coverage --last 50
    └─ runs: git log --oneline -50
    └─ for each commit SHA, runs: git log -1 --format=%B <sha>
    └─ counts commits where body contains "^Spec: " line
    → prints "47/50 commits have spec coverage (94%)"
    → lists uncovered SHAs
```

### `specwarden trace <commit>`

```
specwarden trace abc1234
    └─ git log -1 --format=%B abc1234  → parses "Spec: <id>" line
    └─ reads .claude/specs/<id>.md      → spec text
    └─ reads .claude/decisions/<id>.md  → decisions text
    → prints commit SHA, spec ID, spec body, decisions log
```

### `specwarden git-hook install`

```
specwarden git-hook install
    └─ checks .git/hooks/prepare-commit-msg (must be absent or managed-by: specwarden)
    └─ writes HOOK_SCRIPT to .git/hooks/prepare-commit-msg
    └─ sets executable bits (u+x, g+x, o+x)
    → prints "installed: .git/hooks/prepare-commit-msg"
```

## Data flow: hooks during a Claude Code session

The hooks are invoked by Claude Code when the configured tool events fire. The `settings.json` written by `specwarden init` wires them:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [
          {"type": "command", "command": "/abs/python3 /abs/specwarden/hooks/pre_tool_use.py"}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [
          {"type": "command", "command": "/abs/python3 /abs/specwarden/hooks/post_tool_use.py"}
        ]
      }
    ],
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "/abs/python3 /abs/specwarden/hooks/session_start.py"}]}
    ]
  }
}
```

### PreToolUse flow

```
Claude calls Edit/Write/MultiEdit/NotebookEdit
    │
    ▼
Claude Code → stdin JSON → <abs python> <abs pre_tool_use.py>
    │
    ├─ tool_name not in EDITING_TOOLS?
    │      → allow
    │
    ├─ SPECWARDEN_QUICKFIX=1?
    │      → allow
    │
    ├─ .claude/specs/active absent or empty?
    │      → deny "no active spec"
    │
    ├─ spec file missing, or four sections still unwritten?
    │      → deny "still has unwritten sections: ..."
    │
    └─ spec active and written
           → allow

  every decision is nested:
    {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                            "permissionDecision": "allow"|"deny",
                            "permissionDecisionReason": "..."}}
  denials also carry legacy top-level {"decision": "block", "reason": "..."}
```

### PostToolUse flow

```
Edit/Write/MultiEdit/NotebookEdit completes
    │
    ▼
Claude Code → stdin JSON → <abs python> <abs post_tool_use.py>
    │
    ├─ tool_name not in EDITING_TOOLS?  → exit 0 (no-op)
    ├─ no active spec?                  → exit 0 (no-op)
    │
    └─ active spec exists
           → derives file_path and line_range from tool_input
           → appends block to .claude/decisions/<spec-id>.md
           → exit 0
```

### SessionStart flow

```
Claude Code session opens
    │
    ▼
Claude Code → <abs python> <abs session_start.py>
    │
    ├─ .claude/specs/active exists and non-empty?
    │      → stdout: "specwarden: active spec is <id>\n"
    │
    └─ otherwise
           → stdout: "specwarden: no active spec. Run `/spec <slug>`...\n"
```

## The `Spec:` trailer and `prepare-commit-msg`

The `prepare-commit-msg` git hook (installed by `specwarden git-hook install`) appends a `Spec:` trailer to commit messages while a spec is active:

```bash
ACTIVE_FILE="$(git rev-parse --show-toplevel)/.claude/specs/active"
if [ -f "$ACTIVE_FILE" ]; then
    SPEC_ID="$(tr -d '[:space:]' < "$ACTIVE_FILE")"
    if [ -n "$SPEC_ID" ] && ! grep -qxF "Spec: $SPEC_ID" "$COMMIT_MSG_FILE"; then
        printf "\nSpec: %s\n" "$SPEC_ID" >> "$COMMIT_MSG_FILE"
    fi
fi
```

The hook uses `grep -qxF` (whole-line fixed-string match) to avoid duplicating the trailer if it is already present. The `printf "\\nSpec: %s\\n"` construction is intentional: Python writes a literal `\n` to disk, which bash `printf` interprets as a newline, keeping the git trailer format correct.

`specwarden coverage` and `specwarden trace` both read `Spec:` trailers from `git log --format=%B` output to reconstruct the chain. The format is `Spec: <spec-id>` on its own line, no quotes.

## Why hooks live in the wheel

`specwarden init` records each hook as `<sys.executable> <absolute script path>`.

Through 0.1.0 it wrote `python -m specwarden.hooks.pre_tool_use`, on the reasoning
that pipx puts specwarden on PATH. That reasoning was wrong: pipx adds the
*console script* to PATH, not the *package* to any interpreter's module path, so
`-m` could not resolve it. A bare `python` is also absent on stock macOS and
Debian. Either way the hook exited 1 — which `PreToolUse` treats as a
non-blocking error — so the gate vanished without a sound.

Each hook module is self-contained: it imports only from the standard library and
inlines the `_active_spec_id()` helper rather than importing from
`specwarden.paths`. That is what makes invocation by file path viable — the
scripts do not need the package to be importable at all, only readable.

## Quick-fix mode

Setting `SPECWARDEN_QUICKFIX=1` in the environment before invoking Claude Code bypasses the PreToolUse check. The PostToolUse hook still runs but finds no active spec and exits without logging. Use this for edits where a full spec is genuine overhead — typo fixes, dependency bumps — and accept that those commits will appear as uncovered in `specwarden coverage` output.

For edge cases, wiring, and troubleshooting, see `docs/HOOKS.md` and `docs/TROUBLESHOOTING.md`.
