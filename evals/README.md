# Eval Fixtures — Methodology

## Purpose

These fixtures let a benchmark runner extract a known starting state, hand it
to a Claude Code session with a fixed prompt, and measure what happens. The
goal is to quantify how spec-trace changes Claude Code's behaviour across a
set of concrete, reproducible coding tasks.

## Structure

Each fixture lives in `evals/fixtures/task_NNN_<slug>/` and contains four
pieces:

| File | Role |
|---|---|
| `starting_state.tar.gz` | Tarball of the starting repo (no leading directory inside the archive). The runner extracts this into a temp dir before each trial. |
| `starting_state/` | Unpacked source committed for inspection. The tarball is what the runner actually uses. |
| `prompt.md` | The literal user message handed to Claude Code. |
| `expected.md` | Reviewer guidance: what a correct change does and does not do, and what to watch for. |

## The 5 Tasks

| ID | Slug | What it tests |
|---|---|---|
| 001 | add_auth | Whether Claude adds JWT auth to a Flask app without scope creep (no DB, no tests, no config framework). |
| 002 | refactor_logger | Whether Claude unifies five per-level print helpers into a single `log(level, message)` function without touching message text. |
| 003 | add_test_suite | Whether Claude writes a pytest suite for a CLI using only stdlib + pytest, without modifying the CLI itself. |
| 004 | fix_race | Whether Claude correctly fixes a documented threading race condition and adds a deterministic test for it. |
| 005 | add_endpoint | Whether Claude adds a new route that touches only the two files the prompt specifies (db.py, routes.py) and leaves models.py alone. |

## Three-Arm Benchmark Structure

Each task is run in three arms. The runner (`evals/run_eval.py`) launches
`claude --bare` for every arm so the host's plugins, skills, and
`CLAUDE.md` cannot contaminate the session; arm-specific surface is
introduced via explicit flags.

| Arm | Skill in context | Hooks active | Flags |
|---|---|---|---|
| A (control) | no | no | `--bare`, full tool access via `--dangerously-skip-permissions` |
| B (advisory) | yes (via `--append-system-prompt-file SKILL.md`) | no | A's flags + the SKILL.md system prompt |
| C (enforced) | yes | yes (`PreToolUse`, `PostToolUse`, `SessionStart` from `.claude/settings.json`) | B's flags + `--settings <workdir>/.claude/settings.json` |

Arm B isolates the contribution of *mere guidance* — does Claude behave
better when it merely knows the spec-trace skill exists? Arm C measures
the contribution of mechanical enforcement (the PreToolUse hook blocks
edits with no active spec; PostToolUse appends each accepted edit to the
decisions log).

For arm C, no spec is pre-activated. The PreToolUse hook will return
`ask` on the first edit, prompting Claude to invoke `/spec` and create
one before proceeding — the same loop a human developer would see.

## Metrics

The runner and measurement scripts (Phase 9.2 / 9.3) capture:

- Files modified (set diff against starting state).
- Whether the change compiles / imports cleanly.
- Interruption count (how many times Claude asked a clarifying question).
- Scope creep (files modified that are outside the expected set).
- Reviewer score (0–3) from `expected.md` checklist.

## Reproducibility

Any reviewer can replay a trial by extracting the tarball into a fresh
directory and running Claude Code with the text in `prompt.md` as the
opening message.

```
mkdir /tmp/trial && tar -xzf evals/fixtures/task_001_add_auth/starting_state.tar.gz -C /tmp/trial
cd /tmp/trial
# open Claude Code, paste prompt.md contents
```
