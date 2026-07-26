---
name: specwarden
description: Use when starting any non-trivial code change in this repo — refuses Edit/Write until a one-page spec is written; logs every accepted edit with a backlink. Activates on `/spec`, `/trace`, `/coverage`, `/spec-help`.
---

# specwarden

> Every code change traces back to a written spec. Enforced by hooks, not vibes.

## What this does

specwarden enforces a spec-first discipline: before any Edit or Write tool call lands, a structured one-page spec must exist and be marked ready. The PreToolUse hook reads `.claude/specs/active` on every tool call; if no spec is active, the hook denies the call and tells you why. This makes the discipline mechanical rather than voluntary.

The gate's reach is exactly its matcher: `Edit|Write|MultiEdit|NotebookEdit`. Shell commands are not matched, so writing a file through `cat >`, `sed -i` or `tee` bypasses both the gate and the decisions log. Do not route edits through Bash to get around a missing spec — write the spec. If a spec would genuinely be absurd for the change, `SPECWARDEN_QUICKFIX=1` is the sanctioned bypass and leaves an honest uncovered commit behind.

Once a spec is active, every edit is logged to `.claude/decisions/<spec-id>.md` with a timestamp and a reference back to the spec. When you commit, a `Spec: <id>` trailer is appended automatically (requires `specwarden git-hook install`). The result is a chain you can walk in either direction: from a commit to its spec, or from a spec to every file it touched.

## Slash commands

### `/spec <slug>`

Creates a new spec file at `.claude/specs/<slug>.md` from the four-section template and writes the slug to `.claude/specs/active`. Until all four sections are filled in and you type `ready`, the PreToolUse hook blocks any Edit or Write call with a message indicating which sections are still empty.

### `/trace [<commit>]`

Prints the full chain for a given commit: commit SHA, the `Spec:` trailer, the spec file, and the corresponding decisions log. Defaults to HEAD when no commit is specified.

### `/coverage [--last N]`

Scans recent commits (all commits, or the last N if `--last N` is given) and reports how many carry a `Spec:` trailer. Output format: `covered/total commits have spec coverage (pct%)`, followed by a list of uncovered SHAs.

### `/spec-help`

Prints a one-page quick-reference card: the four slash commands, the spec template, the quick-fix escape hatch, and the path layout.

## The four-section spec template

```markdown
# <Spec ID>: <Short Title>

**Created:** <ISO timestamp>
**Status:** active | completed | abandoned
**Author:** <human name>

## Assumptions
What we are taking as given. If any of these turns out to be false, the spec is
invalid and must be revised before more code lands.

- Assumption 1
- Assumption 2

## Scope
What this change is. Concrete, files-and-functions level if possible.

- We will modify X
- We will add Y
- We will not touch Z

## Non-goals
What this change is explicitly not. The point of this section is to prevent
scope creep mid-implementation.

- We will not refactor adjacent module M
- We will not change the public API of P

## Success criteria
How we will know we are done. Must be checkable.

- [ ] Test T passes
- [ ] Manual scenario S works
- [ ] Documentation D is updated
```

## The discipline

1. User describes a feature or fix.
2. You invoke `/spec <slug>` and fill in all four sections in conversation. Push back on vague assumptions, surface trade-offs, propose non-goals to prevent scope creep.
3. User reviews the spec and types `ready`.
4. You proceed to edit. Each edit is appended to `.claude/decisions/<spec-id>.md` with a timestamp.
5. When the work is done, run `specwarden done` from the terminal (or call the `mark_done` helper) to flip the spec status to `completed`.
6. Commits made while the spec is active automatically carry a `Spec: <id>` trailer if `specwarden git-hook install` was run beforehand.

The spec is not a bureaucratic artifact — it is the conversation record that prevents you and the human from talking past each other mid-implementation. Write it as if someone will read it six months from now to understand why a particular decision was made.

## Quick-fix mode

For edits where a full spec is genuine overhead — typo fixes, dependency version bumps, comment rewording — set `SPECWARDEN_QUICKFIX=1` in the environment before invoking Claude Code. The PreToolUse hook will allow Edit and Write calls without an active spec. The decisions log will not capture the edit. Use sparingly; the coverage report will mark these commits as uncovered.

## Hook contract version

Verified against Claude Code 2.1.218.

- `PreToolUse` writes the decision to stdout **nested under `hookSpecificOutput`**:

  ```json
  {
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "deny",
      "permissionDecisionReason": "specwarden: no active spec."
    }
  }
  ```

  A bare top-level `permissionDecision` is parsed as an unknown key and silently
  ignored — the edit proceeds. On a deny, specwarden also emits the legacy
  top-level `decision: "block"` / `reason` pair, which older hosts honour.
- `PostToolUse` returns nothing (exit 0); side effects happen on disk.
- `SessionStart` writes a banner to stdout.

Exit codes matter as much as the payload: for `PreToolUse`, **only exit 2 blocks**.
Exit 1 is a non-blocking error, so a hook that crashes fails *open* and enforcement
silently disappears. specwarden exits 0 and carries the decision in the payload.

`tests/test_pre_tool_use.py` asserts this exact wire format, including that no bare
top-level `permissionDecision` is emitted. Those assertions are what catch contract
drift; there is no automated check against unreleased Claude Code versions, so a
future release could still change the contract without CI noticing.

## Files this skill writes

- `.claude/specs/<spec-id>.md` — the spec document, created by `/spec` or `specwarden new`.
- `.claude/specs/active` — single line containing the currently active spec ID; read by the PreToolUse hook on every tool call.
- `.claude/decisions/<spec-id>.md` — append-only log of every edit authorized under the spec.
- `.claude/settings.json` — hook wiring; created once by `specwarden init` and not modified again by the skill.

## Out of scope for v1

The skill does not generate specs on behalf of the user. The human writes the spec; that is the forcing function. Auto-generated specs would remove the discipline the tool is designed to create. This is recorded in the project's own SPEC under "Non-goals" for v1.
