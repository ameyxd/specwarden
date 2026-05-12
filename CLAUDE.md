# specwarden — working notes

This file is the standing context for anyone (human or agent) working on this repo.
Read it before touching code. Update it when conventions change.

## What we are building

`specwarden` is a Claude Code skill plus a set of lifecycle hooks that gate
filesystem edits behind a written spec. It also ships a Python CLI and an
eval suite. The full requirements live in `SPEC_specwarden.md` at the repo
root — that file is the single source of truth for v1 scope.

If anything here drifts from `SPEC_specwarden.md`, the SPEC wins.

## Working directories

| Path | Purpose |
| --- | --- |
| `SPEC_specwarden.md` | Authoritative spec for v1. Treat as read-only unless the user changes scope. |
| `docs/superpowers/plans/` | Implementation plan(s). The active one is `2026-05-07-specwarden-v1.md`. |
| `.claude/skills/specwarden/` | The published skill artifact (SKILL.md, scripts, templates). Ships with the package. |
| `.claude/internal/` | Tracking notes for this build. Gitignored. Worklog, project context, feature specs go here. |
| `src/specwarden/` | Python CLI package. `pipx install specwarden` installs the entry point. |
| `hooks/` | Standalone hook scripts copied into the user repo by `specwarden init`. |
| `evals/` | Three-arm benchmark. Fixtures, runner, results. |
| `examples/` | Reference projects that show specwarden in use. |
| `docs/` | Public-facing markdown docs. |

## Conventions

- Python 3.10+. Use `from __future__ import annotations` and standard library
  where possible. Third-party deps: `typer`, `pytest`. Add more only with a
  reason recorded in the plan.
- Tests live next to code under `tests/<module>/test_<thing>.py`. Use `pytest`,
  not `unittest`. Aim for one assertion per test where practical.
- Format with `ruff format`. Lint with `ruff check`. Both run in CI.
- Markdown is written for engineers reading on a laptop. No marketing tone,
  no superlatives, no AI tells. Headings are sentence case.
- Commits follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`,
  `chore:`, `refactor:`). Subject under 72 chars. No emoji in commits or docs.
  Do not tag releases with a `v` prefix.
- Every commit that lands real code should carry a `Spec: <spec-id>` trailer.
  The CLI is responsible for keeping that easy.
- Keep files small and focused. Split when one file owns more than one job.

## Spec → decisions → commit chain

This is the discipline the project itself tries to enforce, so we eat our own
dog food while building it:

1. Before touching code for a new chunk of work, write a spec under
   `.claude/specs/` (use the four-section template once it exists).
2. Set the active spec in `.claude/specs/active`.
3. Make changes. Each edit gets logged to `.claude/decisions/<spec-id>.md`.
4. Commit with a `Spec: <spec-id>` trailer.

For the bootstrap phase we may write specs by hand because the tooling does
not exist yet. Once the CLI lands (Phase 1 complete), switch to the tooling.

## How to run things

```bash
# Install the package in editable mode for local work
pipx install -e .

# Run tests
pytest

# Lint and format
ruff check .
ruff format .

# Run the eval (slow, costs API tokens)
make eval
```

Until `pyproject.toml` is in place, only the planning files exist. See the
implementation plan for the bootstrap order.

## Things to watch out for

- The Claude Code hook contract (JSON shape, `permissionDecision` values) is
  the integration surface with the host tool. Pin the hook version we target
  in `SKILL.md` and add a CI test that exercises it.
- The `.claude/specs/active` file is the synchronization point between hooks
  and the CLI. Treat it as a single line, no trailing whitespace, no BOM.
- The eval suite uses `claude` headless mode. Document the exact CLI flags
  used so the benchmark is reproducible.
- Do not auto-generate specs. The whole product loses its meaning if specs
  are produced by the same agent the spec is supposed to constrain.

## Out of scope (do not build)

See the SPEC's "Non-goals" section. Short list: no web UI, no Jira-style
project management, no team features, no AI-generated specs, no external
tracker integrations, no per-language templates.

## Where to write progress

- Plan progress: tick boxes in `docs/superpowers/plans/2026-05-07-specwarden-v1.md`.
- Session log: `.claude/internal/WORKLOG.md` (append at end of each session).
- Cross-session state: `.claude/internal/PROJECT_CONTEXT.md`.
- Per-feature notes: `.claude/internal/FEATURE_SPECS.md`.
