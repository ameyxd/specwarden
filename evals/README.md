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

Each task is run in three arms:

- **Arm A (baseline):** Claude Code with no spec-trace installed. The session
  starts from a clean extraction of `starting_state.tar.gz`.
- **Arm B (spec-trace, no active spec):** spec-trace is installed and
  initialised in the repo, but no spec is active. Hooks fire but emit no
  active-spec context.
- **Arm C (spec-trace, active spec):** spec-trace is installed and a spec
  matching the task is activated before the session starts.

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
