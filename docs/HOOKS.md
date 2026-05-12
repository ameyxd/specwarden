# Hooks

specwarden wires three Claude Code lifecycle hooks: `PreToolUse`, `PostToolUse`, and `SessionStart`. This document describes the exact JSON contract each hook handles, the edge cases, and how to verify or disable them.

For the data-flow diagrams showing how these hooks fit into the overall architecture, see `docs/ARCHITECTURE.md`.

## Hook contract version

This skill targets the Claude Code hook contract published in 2026-Q1 (present in `claude` 2.1.x releases). The contract defines:

- `PreToolUse` hooks: read a JSON payload from stdin, write a JSON decision to stdout, exit 0.
- `PostToolUse` hooks: read a JSON payload from stdin, produce side effects, write nothing to stdout, exit 0.
- `SessionStart` hooks: write a banner string to stdout, exit 0.

The `permissionDecision` field accepted values are `"allow"`, `"deny"`, and `"ask"`. specwarden uses `"allow"` and `"ask"` only; it never emits `"deny"` because `"ask"` surfaces the message to the user rather than silently refusing the call.

If the hook contract changes in a later Claude Code release, update `SKILL.md` and these hook scripts accordingly. The CI workflow at `.github/workflows/ci.yml` runs a weekly job exercising the hook contract against the latest published Claude Code release to catch drift early.

## Hook installation

`specwarden init` writes `.claude/settings.json` with the following hook wiring:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [
          {"type": "command", "command": "python -m specwarden.hooks.pre_tool_use"}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [
          {"type": "command", "command": "python -m specwarden.hooks.post_tool_use"}
        ]
      }
    ],
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "python -m specwarden.hooks.session_start"}]}
    ]
  }
}
```

The `matcher` field is a pipe-separated regex applied to `tool_name`. The four editing tools covered are `Edit`, `Write`, `MultiEdit`, and `NotebookEdit`. `SessionStart` has no matcher field — it fires on every session open.

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

if tool_name not in EDITING_TOOLS:
    → {"permissionDecision": "allow"}

if SPECWARDEN_QUICKFIX == "1":
    → {"permissionDecision": "allow"}

if .claude/specs/active is absent or empty:
    → {"permissionDecision": "ask",
       "message": "specwarden: no active spec. Run `/spec <slug>` first..."}

→ {"permissionDecision": "allow"}
```

### Output when no spec is active

```json
{
  "permissionDecision": "ask",
  "message": "specwarden: no active spec. Run `/spec <slug>` first to define what you're building before editing files."
}
```

`"ask"` surfaces the message in the Claude Code UI and prompts the user to decide. The agent sees the message and is expected to invoke `/spec` or `specwarden new` before retrying the edit.

### Output when a spec is active (or quickfix mode)

```json
{"permissionDecision": "allow"}
```

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

If `specwarden init` was never run, `.claude/specs/` does not exist. The PreToolUse hook's `_active_spec_id()` function calls `marker.exists()` on the path; if the path does not exist, it returns `None`, and the hook returns `ask`. The hook does not raise an exception on a missing directory.

### Empty `active` file

If `.claude/specs/active` exists but contains only whitespace, `strip()` returns an empty string, and the hook treats it as absent (returns `ask` from PreToolUse, no-op from PostToolUse).

### Spec ID with unusual characters

The `slugify` function in `spec.py` replaces all non-alphanumeric characters with hyphens, so spec IDs are always of the form `YYYY-MM-DD_<slug>` with only lowercase alphanumerics and hyphens. The `prepare-commit-msg` hook uses `grep -qxF` (fixed-string, whole-line match) to avoid any regex interpretation of the spec ID.

### Quick-fix mode and decisions log

When `SPECWARDEN_QUICKFIX=1`, PreToolUse allows the edit but PostToolUse still runs. PostToolUse checks for an active spec independently; if none is active, it exits without logging. If a spec happens to be active while in quick-fix mode, PostToolUse will still log the edit. This is intentional: quick-fix mode bypasses the gate, not the log.

### Hook command not found

If `python -m specwarden.hooks.pre_tool_use` fails (e.g., `specwarden` is not on the Python path), Claude Code will surface the hook error. See `docs/TROUBLESHOOTING.md` for diagnosis steps.

## Verifying hooks are firing

**Check the decisions log.** After a Claude Code session that made edits with an active spec, inspect `.claude/decisions/<spec-id>.md`. Each edit should have appended a block.

**Check `specwarden status`.** Run `specwarden status` from the repo root. It reports the current active spec. If it reports "no active spec" but you expected one to be active, the `.claude/specs/active` file is absent or empty.

**Inspect the JSONL session log.** Claude Code writes a JSONL log of every session event. Look for `hook_started` and `hook_response` events with `hook_type: "PreToolUse"`. If these events are absent for edit tool calls, the hook is not wired correctly.

**Run the hook manually.** Pipe a hand-crafted payload to verify the hook runs and produces expected output:

```bash
echo '{"tool_name":"Edit","tool_input":{"file_path":"foo.py","old_string":"x","new_string":"y"}}' \
  | python -m specwarden.hooks.pre_tool_use
```

With no active spec, this should print:
```json
{"permissionDecision": "ask", "message": "specwarden: no active spec. Run `/spec <slug>` first to define what you're building before editing files."}
```

After `specwarden activate <id>`, the same command should print:
```json
{"permissionDecision": "allow"}
```

## Disabling and uninstalling

**Disable for one session:** set `SPECWARDEN_QUICKFIX=1` before opening Claude Code. All edit tool calls will be allowed without a spec check.

**Remove hook wiring:** edit `.claude/settings.json` and remove the `PreToolUse`, `PostToolUse`, and `SessionStart` entries. Claude Code reads `settings.json` at session start; changes take effect on next session open.

**Remove the git trailer hook:** run `specwarden git-hook uninstall`. This removes `.git/hooks/prepare-commit-msg` if and only if it contains the `# managed-by: specwarden` marker. If it was installed by something else (or manually modified), the command will refuse to remove it.

**Full removal:** run `specwarden git-hook uninstall`, remove the hooks entries from `.claude/settings.json`, and optionally delete `.claude/specs/` and `.claude/decisions/`. The `specwarden` package itself can be removed with `pipx uninstall specwarden`.
