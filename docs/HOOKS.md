# Hooks

specwarden wires three Claude Code lifecycle hooks: `PreToolUse`, `PostToolUse`, and `SessionStart`. This document describes the exact JSON contract each hook handles, the edge cases, and how to verify or disable them.

For the data-flow diagrams showing how these hooks fit into the overall architecture, see `docs/ARCHITECTURE.md`.

## Hook contract version

Verified against Claude Code 2.1.218.

- `PreToolUse` hooks: read a JSON payload from stdin, write a JSON decision to stdout, exit 0.
- `PostToolUse` hooks: read a JSON payload from stdin, produce side effects, write nothing to stdout, exit 0.
- `SessionStart` hooks: write a banner string to stdout, exit 0.

**The decision must be nested under `hookSpecificOutput`.** Claude Code reads
`hookSpecificOutput.permissionDecision`; a bare top-level `permissionDecision` is
an unrecognised key and is ignored, which means the edit proceeds. specwarden
emitted the top-level shape from its first release until 0.2.0, so its gate never
blocked anything in that period. Accepted values are `"allow"`, `"deny"` and
`"ask"`. specwarden uses `"allow"` and `"deny"`.

`"ask"` is not used. It reads like a softer block, but it is auto-resolved under
`acceptEdits`, `bypassPermissions` and any headless (`-p`) run — precisely the
autonomous settings where a gate is worth having.

**Exit codes matter as much as the payload.** For `PreToolUse`, only **exit 2**
blocks. Exit 1 is a non-blocking error: Claude Code reports it and runs the tool
anyway. A hook that crashes, or cannot start, therefore fails *open*. specwarden
exits 0 and carries the decision in the payload.

If the contract changes in a later Claude Code release, update `SKILL.md`, these
scripts, and `tests/test_pre_tool_use.py`, which asserts the exact wire format
including the absence of a bare top-level `permissionDecision`. Those assertions
are the only drift protection; there is no automated check against unreleased
Claude Code versions.

## Hook installation

`specwarden init` writes `.claude/settings.json` with the following hook wiring:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [
          {"type": "command", "command": "/abs/path/to/python3 /abs/path/to/specwarden/hooks/pre_tool_use.py"}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [
          {"type": "command", "command": "/abs/path/to/python3 /abs/path/to/specwarden/hooks/post_tool_use.py"}
        ]
      }
    ],
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "/abs/path/to/python3 /abs/path/to/specwarden/hooks/session_start.py"}]}
    ]
  }
}
```

Both paths are absolute and resolved at `init` time: the interpreter is the
`sys.executable` that ran `specwarden init`, and the hook is addressed by file
path rather than as `-m specwarden.hooks.<module>`.

That is deliberate, and each half fixes a real failure. A bare `python` does not
exist on stock macOS or Debian. And under `pipx`, specwarden lives in an isolated
venv, so no ambient interpreter can import it — `-m` raises `ModuleNotFoundError`
and exits 1, which does not block, so the gate silently disappears. Addressing
the hook by file path sidesteps package resolution entirely; the hook modules are
stdlib-only and import nothing from specwarden, so they run standalone.

The `matcher` field is a pipe-separated regex applied to `tool_name`. The four editing tools covered are `Edit`, `Write`, `MultiEdit`, and `NotebookEdit`. `SessionStart` has no matcher field — it fires on every session open.

### What the matcher does not cover

Shell commands are not matched. An agent that writes a file with `cat > file`,
`sed -i` or `tee` bypasses both the gate and the decisions log. This is verified
behaviour, not a theoretical gap.

Adding `Bash` to the matcher would deny every shell command without an active
spec — `ls`, `grep`, the test run — so specwarden does not do it. The gate is a
guardrail against an agent that drifts, not a sandbox against one working around
you.

## PreToolUse

**Source:** `src/specwarden/hooks/pre_tool_use.py`

**Fires:** before every `Edit`, `Write`, `MultiEdit`, or `NotebookEdit` tool call.

### Input

Claude Code serializes the pending tool call to stdin as JSON. The fields specwarden reads:

```json
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "src/auth/middleware.py",
    "old_string": "...",
    "new_string": "..."
  }
}
```

For `Write` calls the `tool_input` contains `file_path` and `content` instead of `old_string`/`new_string`. For `MultiEdit` it contains a list of edits. The hook only reads `tool_name`; it does not inspect `tool_input`.

### Decision logic

```python
EDITING_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
REQUIRED_SECTIONS = ("Assumptions", "Scope", "Non-goals", "Success criteria")

if tool_name not in EDITING_TOOLS:
    → allow

if SPECWARDEN_QUICKFIX == "1":
    → allow

if .claude/specs/active is absent or empty:
    → deny "no active spec"

if .claude/specs/<active>.md does not exist:
    → deny "active spec is <id> but the file does not exist"

if any REQUIRED_SECTION has no substantive bullet:
    → deny "spec <id> still has unwritten sections: <names>"

→ allow
```

The section check exists because without it the gate is satisfied by
`specwarden new` followed by `specwarden activate`: two commands, not one word
written, both of which an agent with a shell can run itself. Template `- TODO`
and `- [ ] TODO` placeholders do not count as content.

### Output when no spec is active

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "specwarden: no active spec. Run `/spec <slug>` first to define what you're building before editing files."
  },
  "decision": "block",
  "reason": "specwarden: no active spec. Run `/spec <slug>` first to define what you're building before editing files."
}
```

The top-level `decision`/`reason` pair is the legacy form. Current Claude Code
marks it deprecated for `PreToolUse` but still honours it, and older hosts
understand nothing else, so denials emit both. Note this is `decision`, not
`permissionDecision` — a top-level `permissionDecision` has never been a valid
field in any version, which is exactly why emitting it failed silently.

### Output when the spec is an unfilled template

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "specwarden: spec 2026-07-26_add-utc-flag still has unwritten sections: Assumptions, Scope, Non-goals, Success criteria. Fill them in before editing files. An empty template is not a spec."
  },
  "decision": "block",
  "reason": "..."
}
```

### Output when a spec is active (or quickfix mode)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "specwarden: active spec is 2026-07-26_add-utc-flag."
  }
}
```

Allow decisions carry no legacy keys. Legacy `decision` has no "allow" value —
emitting one would block.

### Quick-fix bypass

Set `SPECWARDEN_QUICKFIX=1` in the shell before starting a Claude Code session. The hook reads `os.environ.get("SPECWARDEN_QUICKFIX")` and short-circuits to `allow` when it equals `"1"`. No decisions log entry is written for edits made in quick-fix mode. The commits will appear as uncovered in `specwarden coverage` output.

```bash
SPECWARDEN_QUICKFIX=1 claude
```

The environment variable is checked per hook invocation, so you can set it mid-session by restarting the session or by adjusting the hook command in `settings.json`. There is no CLI toggle; the environment variable is the interface.

## PostToolUse

**Source:** `src/specwarden/hooks/post_tool_use.py`

**Fires:** after every `Edit`, `Write`, `MultiEdit`, or `NotebookEdit` tool call completes.

### Input

Claude Code serializes the completed tool call (including result) to stdin:

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "src/auth/jwt.py",
    "content": "..."
  },
  "tool_result": "File written successfully"
}
```

The hook reads `tool_name` and `tool_input`. It does not read `tool_result`.

### Behavior

If `tool_name` is not in `EDITING_TOOLS`, the hook exits 0 without writing anything.

If no spec is active (`.claude/specs/active` absent or empty), the hook exits 0 without writing anything. This handles the case where an edit slips through without an active spec (e.g., before `specwarden init` was run, or in quick-fix mode).

If a spec is active, the hook appends a structured block to `.claude/decisions/<spec-id>.md`:

```markdown
## 2026-05-06T14:32:18+00:00
- File: src/auth/jwt.py
- Lines: 1-87 (created)
- Summary: Write on src/auth/jwt.py
- Tool: Write
```

For `Edit` calls (which contain `old_string`), the `Lines` field is `"edit"`. For `Write` calls (which contain `content`), the hook counts newlines to produce a line range like `"1-87 (created)"`.

If the decisions file does not exist yet, the hook writes a header first:

```markdown
# Decisions: 2026-05-06_add-jwt-auth

Append-only log of changes authorized by this spec.

```

Then appends the block. The file is opened in append mode (`"a"`), so concurrent writes from parallel tool calls would interleave — in practice, Claude Code executes tool calls serially within a session.

### Output

The hook writes nothing to stdout. It exits 0 on success, 0 on all handled cases (including missing spec). Non-zero exit codes would surface as hook errors in Claude Code; the hook is designed to never fail on expected inputs.

## SessionStart

**Source:** `src/specwarden/hooks/session_start.py`

**Fires:** once when a Claude Code session opens.

### Behavior

Reads `.claude/specs/active`. If it contains a non-empty spec ID, writes to stdout:

```
specwarden: active spec is 2026-05-06_add-jwt-auth
```

If the file is absent or empty, writes:

```
specwarden: no active spec. Run `/spec <slug>` to define what you're building.
  Spec template sections: Assumptions, Scope, Non-goals, Success criteria.
```

This banner appears in the Claude Code session before any user message. It gives the agent context about the current spec state at the start of the session without requiring the user to ask.

### Output

Plain text to stdout. No JSON. The hook exits 0 in all cases.

## Edge cases

### No `.claude/` directory

If `specwarden init` was never run, `.claude/specs/` does not exist. The PreToolUse hook's `_active_spec_id()` function calls `marker.exists()` on the path; if the path does not exist, it returns `None`, and the hook denies. The hook does not raise an exception on a missing directory.

### Empty `active` file

If `.claude/specs/active` exists but contains only whitespace, `strip()` returns an empty string, and the hook treats it as absent (denies from PreToolUse, no-op from PostToolUse).

### Spec ID with unusual characters

The `slugify` function in `spec.py` replaces all non-alphanumeric characters with hyphens, so spec IDs are always of the form `YYYY-MM-DD_<slug>` with only lowercase alphanumerics and hyphens. The `prepare-commit-msg` hook uses `grep -qxF` (fixed-string, whole-line match) to avoid any regex interpretation of the spec ID.

### Quick-fix mode and decisions log

When `SPECWARDEN_QUICKFIX=1`, PreToolUse allows the edit but PostToolUse still runs. PostToolUse checks for an active spec independently; if none is active, it exits without logging. If a spec happens to be active while in quick-fix mode, PostToolUse will still log the edit. This is intentional: quick-fix mode bypasses the gate, not the log.

### Hook command not found

If the hook command fails to start, Claude Code surfaces a `PreToolUse:Edit hook error` notice — **and runs the tool anyway.** Only exit 2 blocks; a Python
interpreter that cannot find its script exits 2, but a `ModuleNotFoundError`
exits 1, which does not.

This is why `init` writes absolute interpreter and script paths. It is also the
most dangerous failure mode in the whole system: a broken gate is indistinguishable
from an absent one unless you read the transcript. See `docs/TROUBLESHOOTING.md`.

## Verifying hooks are firing

**Check the decisions log.** After a Claude Code session that made edits with an active spec, inspect `.claude/decisions/<spec-id>.md`. Each edit should have appended a block.

**Check `specwarden status`.** Run `specwarden status` from the repo root. It reports the current active spec. If it reports "no active spec" but you expected one to be active, the `.claude/specs/active` file is absent or empty.

**Inspect the JSONL session log.** Claude Code writes a JSONL log of every session event. Look for `hook_started` and `hook_response` events with `hook_type: "PreToolUse"`. If these events are absent for edit tool calls, the hook is not wired correctly.

**Run the hook manually.** Pipe a hand-crafted payload to verify the hook runs and produces expected output:

```bash
echo '{"tool_name":"Edit","tool_input":{"file_path":"foo.py","old_string":"x","new_string":"y"}}' \
  | "$(python3 -c "import json;print(json.load(open('.claude/settings.json'))['hooks']['PreToolUse'][0]['hooks'][0]['command'])")"
```

Running the command exactly as `settings.json` records it is the point: it
verifies the wiring, not just the module.

With no active spec, this should print a nested `deny`:
```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "specwarden: no active spec. ..."}, "decision": "block", "reason": "..."}
```

After activating a spec **with all four sections written**, the same command
should print a nested `allow`.

If you see a bare top-level `permissionDecision` with no `hookSpecificOutput`
wrapper, the gate is not working regardless of what the decision says.

## Disabling and uninstalling

**Disable for one session:** set `SPECWARDEN_QUICKFIX=1` before opening Claude Code. All edit tool calls will be allowed without a spec check.

**Remove hook wiring:** edit `.claude/settings.json` and remove the `PreToolUse`, `PostToolUse`, and `SessionStart` entries. Claude Code reads `settings.json` at session start; changes take effect on next session open.

**Remove the git trailer hook:** run `specwarden git-hook uninstall`. This removes `.git/hooks/prepare-commit-msg` if and only if it contains the `# managed-by: specwarden` marker. If it was installed by something else (or manually modified), the command will refuse to remove it.

**Full removal:** run `specwarden git-hook uninstall`, remove the hooks entries from `.claude/settings.json`, and optionally delete `.claude/specs/` and `.claude/decisions/`. The `specwarden` package itself can be removed with `pipx uninstall specwarden`.
