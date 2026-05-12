---
name: specwarden
description: Use when starting any non-trivial code change in this repo — refuses Edit/Write until a one-page spec is written; logs every accepted edit with a backlink. Activates on `/spec`, `/trace`, `/coverage`, `/spec-help`.
---

# specwarden

> Every code change traces back to a written spec. Enforced by hooks, not vibes.

## What this does

specwarden enforces a spec-first discipline: before any Edit or Write tool call lands, a structured one-page spec must exist and be marked ready. The PreToolUse hook reads `.claude/specs/active` on every tool call; if no spec is active, the hook blocks the call and tells you why. This makes the discipline mechanical rather than voluntary.

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

This skill targets the Claude Code hook contract published in 2026-Q1:

- `PreToolUse` returns `{"permissionDecision": "allow" | "deny" | "ask", "message": "..."}` over stdout.
- `PostToolUse` returns nothing (exit 0); side effects happen on disk.
- `SessionStart` writes a banner to stdout.

If the hook contract changes in a later Claude Code release, this skill must be updated to match. The CI workflow at `.github/workflows/ci.yml` runs a weekly job that exercises the hook contract against the latest published Claude Code release to catch drift early.

## Files this skill writes

- `.claude/specs/<spec-id>.md` — the spec document, created by `/spec` or `specwarden new`.
- `.claude/specs/active` — single line containing the currently active spec ID; read by the PreToolUse hook on every tool call.
- `.claude/decisions/<spec-id>.md` — append-only log of every edit authorized under the spec.
- `.claude/settings.json` — hook wiring; created once by `specwarden init` and not modified again by the skill.

## Out of scope for v1

The skill does not generate specs on behalf of the user. The human writes the spec; that is the forcing function. Auto-generated specs would remove the discipline the tool is designed to create. This is recorded in the project's own SPEC under "Non-goals" for v1.
