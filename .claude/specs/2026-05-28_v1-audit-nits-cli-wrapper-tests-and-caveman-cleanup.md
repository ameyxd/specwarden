# 2026-05-28_v1-audit-nits-cli-wrapper-tests-and-caveman-cleanup: v1 audit nits CLI wrapper tests and Caveman cleanup

**Created:** 2026-05-28T18:44:06+00:00
**Status:** completed
**Author:** Amey Ambade

## Assumptions

- `.claude/internal/V1_AUDIT.md` is still the authoritative pre-launch
  audit. It flags exactly two non-blocking nits:
  (a) `coverage` and `trace` CLI wrappers in `src/specwarden/cli.py`
  lack direct CLI-layer tests (existing coverage is module-level);
  (b) the Caveman section in `docs/COMPARISONS.md` was written from
  the SPEC's secondhand reference, not from the Caveman repo.
- The current test suite is 63 passing under
  `PYTHONPATH=src .venv/bin/python -m pytest -q`. Adding tests must
  keep that count monotonic and the ruff check clean.
- The Python 3.14 / hatchling editable-install `.pth` quirk is a
  separate, pre-existing issue (documented in WORKLOG and
  NEXT_SESSION). Not in scope here; CLI invocation uses the
  documented `PYTHONPATH=src python -m specwarden.cli` fallback.

## Scope

- `tests/test_cli.py`: add two new tests at the bottom of the file,
  next to the existing CliRunner tests.
  - `test_coverage_reports_against_real_commits` — initializes a
    real git repo under `tmp_path`, makes two commits (one with a
    `Spec: <id>` trailer, one without), invokes
    `app, ["coverage", "--last", "10", "--root", str(tmp_path)]`,
    asserts exit code 0 and that stdout contains the
    `"N/M commits have spec coverage"` line plus the uncovered SHA
    prefix.
  - `test_trace_with_active_spec_succeeds` — initializes a real git
    repo, runs `specwarden init` + `new` + `activate` via the CLI to
    produce a real spec file, writes a decisions-log entry for that
    spec, makes a commit whose message body carries
    `Spec: <spec-id>`, invokes
    `app, ["trace", "HEAD", "--root", str(tmp_path)]`, asserts exit
    code 0 and that stdout contains the spec id and the `---`
    separators emitted by `trace_commit`.
- `docs/COMPARISONS.md`: rewrite only the Caveman section
  (`## Caveman` through the section break before
  `## Summary table`). Replace specific reception claims ("5K+ stars
  quickly", "10K upvotes on r/ClaudeAI") with neutral structural
  language. Keep the "what shares" / "what differs" / "when to use
  both" subsection structure. Update the Summary-table row for
  Caveman only if a column claim no longer holds; if it still holds
  structurally, leave the row alone.
- `.claude/internal/V1_AUDIT.md`: tick both nits closed in the
  "Remaining work" column for DoD #1 row and in the post-launch
  notes if present.
- `.claude/internal/WORKLOG.md`: append a single new entry
  documenting the change and the spec ID.
- One commit, conventional-commit format
  (`test(cli): ...` or `chore: close v1 audit nits ...`), with a
  `Spec: 2026-05-28_v1-audit-nits-cli-wrapper-tests-and-caveman-cleanup`
  trailer in the body.

## Non-goals

- Not fixing the Python 3.14 / hatchling editable-install `.pth`
  quirk. That is a separate issue and deserves its own spec.
- Not adding tests for any command other than `coverage` and
  `trace`. The audit named exactly those two.
- Not running the Caveman repo through a fact-finding fetch.
  The user explicitly chose "Replace the secondhand claims with
  neutral language" over the verify-and-correct option.
- Not changing the comparison structure or summary table for
  GitHub Spec Kit, CLAUDE.md, Cursor, or MCP. Only the Caveman
  section is in scope.
- Not bumping the package version. This is launch-prep polish, not
  a release.

## Success criteria

- [ ] `PYTHONPATH=src .venv/bin/python -m pytest -q` reports
      65 passed (was 63).
- [ ] `uv run ruff check .` is clean.
- [ ] `uv run ruff format --check .` is clean.
- [ ] `docs/COMPARISONS.md` Caveman section contains no specific
      star count or upvote claim. The "what shares" / "what
      differs" framing remains intact.
- [ ] `.claude/internal/V1_AUDIT.md` shows both nits resolved.
- [ ] One git commit lands with the `Spec:` trailer pointing at
      this spec id. `git log -1 --format=%B | grep -F 'Spec: 2026-05-28_v1-audit-nits-cli-wrapper-tests-and-caveman-cleanup'`
      returns a match.
- [ ] Spec marked done via
      `python -m specwarden.cli done --root .` after the commit
      lands. `.claude/specs/active` removed; the spec file's
      status frontmatter reads `completed`.
