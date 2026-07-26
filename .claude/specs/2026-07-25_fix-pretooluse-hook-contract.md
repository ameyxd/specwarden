# 2026-07-25_fix-pretooluse-hook-contract: Fix the PreToolUse hook wire format

**Created:** 2026-07-25
**Status:** active
**Author:** Amey Ambade

## Assumptions
What we are taking as given. If any of these turns out to be false, the spec is invalid and must be revised before more code lands.

- Claude Code 2.1.218 honours `hookSpecificOutput.permissionDecision` for PreToolUse and
  silently ignores a bare top-level `permissionDecision`. Verified live: an identical
  session with a top-level `deny` completed the edit; the nested `deny` blocked it.
- The legacy top-level `decision: "block"` / `reason` pair still blocks today. The shipped
  binary's own help text marks it "deprecated for PreToolUse", not removed.
- `deny` is the behaviour the README and SKILL.md already describe ("no edit lands until
  the spec is active"). `ask` was never the intended contract, and is bypassed entirely
  under `acceptEdits` / `bypassPermissions` / headless runs.
- The hook command written by `specwarden init` must be runnable from the user's repo.
  `python -m specwarden.hooks.pre_tool_use` is not, under either a pipx install (module
  isolated in its own venv) or a stock macOS PATH (no `python` binary).

## Scope
What this change is. Concrete, files-and-functions level if possible.

- `src/specwarden/hooks/pre_tool_use.py`: emit `hookSpecificOutput` with `hookEventName`,
  `permissionDecision`, `permissionDecisionReason`. Switch the no-active-spec decision from
  `ask` to `deny`. Include legacy `decision`/`reason` alongside on deny only.
- `src/specwarden/cli.py`: write hook commands using the absolute interpreter path
  (`sys.executable`) so pipx and python3-only hosts both resolve the module.
- `tests/test_pre_tool_use.py`: assert the exact wire format — nested keys, `hookEventName`,
  and the absence of a bare top-level `permissionDecision`.
- `tests/test_cli.py`: assert `init` writes an absolute, resolvable interpreter path.
- `README.md`: correct the benchmark claim; correct enforcement wording.
- `.claude/skills/specwarden/SKILL.md`: correct the documented hook contract on line 91.

## Non-goals
What this change is explicitly not. The point of this section is to prevent scope creep.

- No change to `measure.py` to compute true out-of-scope edits. That needs a declared
  in-scope file set per fixture; proposed separately, not built here.
- No re-run of the eval. The README wording is corrected to match what the existing run
  actually measured.
- No new `specwarden-hook` console script. `sys.executable` solves the same problem
  without a packaging change.
- No configuration knob for ask-vs-deny.

## Success criteria
How we will know we are done. Must be checkable.

- [ ] A live Claude Code session with no active spec has its Edit blocked, and the model
      reports the specwarden message.
- [ ] `pytest` passes, and the new wire-format test fails if the hook reverts to the
      top-level shape.
- [ ] `ruff check` and `ruff format --check` clean.
- [ ] README contains no claim of "out-of-scope file modifications" unsupported by
      `measure.py`.
