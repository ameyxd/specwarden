# Troubleshooting

This document covers failure modes encountered during development and reported by early users. Each entry follows the format: symptom, cause, fix.

For hook JSON contracts and wiring details, see `docs/HOOKS.md`. For the overall architecture and how the pieces connect, see `docs/ARCHITECTURE.md`.

---

## `specwarden --help` reports `ModuleNotFoundError`

**Symptom:**

```
$ specwarden --help
Traceback (most recent call last):
  ...
ModuleNotFoundError: No module named 'specwarden'
```

Or the `specwarden` binary runs but immediately crashes before printing the help text.

**Cause:**

pipx installs packages into an isolated virtual environment and adds the entry-point binary to `~/.local/bin`. The binary invokes the interpreter inside the isolated venv, so `specwarden` should always be importable when run via the pipx entry point. This error typically means one of:

1. The package was installed with `pip install -e .` (editable install) rather than `pipx`, and the `.pth` file that editable installs write to `site-packages` is not being processed. This is more common on Python 3.14+ where `.pth` processing behavior changed.
2. The `PYTHONPATH` in the environment is set to a value that shadows the package.
3. The binary in `PATH` is a stale wrapper pointing at a now-deleted venv.

**Fix:**

If you installed with `pip install -e .`:

```bash
pip install -e '.[dev]' --force-reinstall --no-deps
```

Or bypass `.pth` processing entirely by setting `PYTHONPATH`:

```bash
export PYTHONPATH=/path/to/specwarden/src
specwarden --help
```

If you used pipx:

```bash
pipx uninstall specwarden
pipx install specwarden
```

If you installed from a local checkout in editable mode via pipx:

```bash
pipx uninstall specwarden
pipx install -e /path/to/specwarden
```

Check which `specwarden` binary is on your PATH:

```bash
which specwarden
```

If it points somewhere unexpected (e.g., inside a venv that no longer exists), remove or fix that entry.

---

## PreToolUse hook does not fire when expected

**Symptom:**

Claude Code makes `Edit` or `Write` calls without triggering the specwarden gate. Edits go through even with no active spec. No `hook_started` events appear in the JSONL session log for PreToolUse.

**Cause A — matcher regex not matching tool name.**

The matcher in `settings.json` is `"Edit|Write|MultiEdit|NotebookEdit"`. If the matcher is malformed (e.g., a typo, extra whitespace, wrong field name), Claude Code will not invoke the hook for those tool names.

**Fix A:**

Inspect `.claude/settings.json` and confirm the PreToolUse entry looks exactly like this:

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
    ]
  }
}
```

Run `specwarden init` again (it will not overwrite an existing file); if you have customized `settings.json`, merge the PreToolUse block by hand.

**Cause B — `python` on PATH does not resolve `specwarden`.**

The hook command is `python -m specwarden.hooks.pre_tool_use`. Claude Code inherits the PATH and environment of the process that launched it. If `python` resolves to a system interpreter that does not have `specwarden` installed, the hook command will fail or produce a `ModuleNotFoundError`, and Claude Code may silently allow the edit rather than surfacing the failure.

**Fix B:**

Check which Python is on the PATH that Claude Code sees:

```bash
which python
python -c "import specwarden; print(specwarden.__file__)"
```

If `specwarden` is not importable, either install it into that Python environment or change the hook command in `settings.json` to use an absolute path to the interpreter:

```json
{"type": "command", "command": "/home/alice/.local/pipx/venvs/specwarden/bin/python -m specwarden.hooks.pre_tool_use"}
```

**Cause C — wrong `settings.json` being loaded.**

Claude Code resolves `settings.json` from the project directory. If you opened Claude Code from a directory other than the repo root, it may be loading a different settings file (or none at all).

**Fix C:**

Always open Claude Code from the repo root, or pass `--settings <path-to-.claude/settings.json>` explicitly.

**Cause D — Claude Code version predates the 2026-Q1 hook contract.**

Very old Claude Code versions (before 2.1.x) used a different hook registration format.

**Fix D:**

```bash
claude --version
```

Update to a 2.1.x release or later.

---

## `specwarden init` refuses to write `settings.json`

**Symptom:**

```
$ specwarden init
initialized: .claude/ (settings.json already exists; left alone)
```

The hook wiring is not present in the existing `settings.json`.

**Cause:**

`specwarden init` will not overwrite an existing `settings.json`. This is by design: the file may contain other project-specific settings (MCP server configuration, other hook registrations) that would be lost by a blind overwrite.

**Fix:**

Open `.claude/settings.json` and merge the hook entries by hand. Add the `PreToolUse`, `PostToolUse`, and `SessionStart` blocks from `docs/HOOKS.md` into the existing `hooks` object. If there is no `hooks` key yet, add it at the top level.

If you want to start fresh and the existing `settings.json` has nothing you need:

```bash
rm .claude/settings.json
specwarden init
```

---

## `prepare-commit-msg` installed but no `Spec:` trailer appearing

**Symptom:**

`specwarden git-hook install` ran without error. Commits are being made while a spec is active. But `git log --format=%B HEAD` does not show a `Spec:` line.

**Cause A — `.claude/specs/active` absent or empty at commit time.**

The hook reads `.claude/specs/active` at the moment `git commit` is invoked. If the spec was deactivated (by `specwarden done` or by manually deleting the file) before committing, the trailer is not appended.

**Fix A:**

```bash
cat .claude/specs/active
```

If it is empty or missing, activate the spec before committing:

```bash
specwarden activate <spec-id>
git commit --amend --no-edit    # amend the most recent commit to add the trailer
```

**Cause B — hook file not executable.**

`specwarden git-hook install` sets executable bits, but if the file was copied or reset (e.g., by a `git checkout` on the hooks directory, or a tool that strips executable bits), the hook will not run.

**Fix B:**

```bash
ls -l .git/hooks/prepare-commit-msg
chmod +x .git/hooks/prepare-commit-msg
```

**Cause C — git `core.hooksPath` points elsewhere.**

If the repository has a `core.hooksPath` configured (common in monorepos with shared hooks), git will look for hooks in the configured path, not `.git/hooks/`.

**Fix C:**

```bash
git config core.hooksPath
```

If it returns a non-default path, either install the specwarden hook there:

```bash
specwarden git-hook install --root /path/to/repo
# then move .git/hooks/prepare-commit-msg to the configured hooksPath
```

Or, if you control the hooks path, ensure `prepare-commit-msg` in that path contains (or sources) the specwarden hook logic from `src/specwarden/git_hook.py`.

**Cause D — existing `prepare-commit-msg` hook not managed by specwarden.**

If a `prepare-commit-msg` hook existed before `specwarden git-hook install` was run, `install_hook` raises a `RuntimeError` and does not overwrite it. The install command would have printed an error; the hook was never written.

**Fix D:**

Inspect the existing hook:

```bash
cat .git/hooks/prepare-commit-msg
```

If it does not contain the specwarden logic, merge by hand: append the block from `src/specwarden/git_hook.py` (the `HOOK_SCRIPT` constant) to the existing hook file, then make it executable.

---

## Decisions log not appending

**Symptom:**

Edits are going through (PreToolUse is allowing them), but `.claude/decisions/<spec-id>.md` is either absent or not growing after edits.

**Cause A — PostToolUse hook not wired.**

The `settings.json` may be missing the `PostToolUse` block, or the matcher may exclude the tool being used.

**Fix A:**

Verify the PostToolUse entry exists in `.claude/settings.json`:

```json
"PostToolUse": [
  {
    "matcher": "Edit|Write|MultiEdit|NotebookEdit",
    "hooks": [
      {"type": "command", "command": "python -m specwarden.hooks.post_tool_use"}
    ]
  }
]
```

Run the hook manually to confirm it works:

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"foo.py","content":"x\ny\n"}}' \
  | python -m specwarden.hooks.post_tool_use
```

With an active spec, this should append a block to `.claude/decisions/<spec-id>.md` and exit 0.

**Cause B — no active spec when edits run.**

PostToolUse checks for an active spec independently of PreToolUse. If the active file was cleared between the PreToolUse call and the PostToolUse call (unlikely but possible if two processes modify the file), PostToolUse will exit without logging.

**Fix B:**

```bash
specwarden status
```

Ensure the spec is still active. Re-activate if needed.

**Cause C — write permission on `.claude/decisions/`.**

In some CI or containerized environments, the `.claude/` directory may be read-only.

**Fix C:**

```bash
ls -la .claude/
```

Ensure the running user has write access to `.claude/decisions/`.

---

## `specwarden coverage` shows 0% on a repo with specwardend commits

**Symptom:**

```
$ specwarden coverage --last 20
0/20 commits have spec coverage (0%)
uncovered:
  abc123456789
  ...
```

But the commits clearly have `Spec:` lines in their messages.

**Cause:**

`specwarden coverage` calls `git log --oneline -N` to get commit SHAs, then calls `git log -1 --format=%B <sha>` on each SHA to read the full commit body. It looks for lines matching the pattern `Spec: ` (case-sensitive, at the start of a line).

If the `Spec:` trailer was added with different casing, extra whitespace, or a different separator (e.g., `spec:` lowercase, or `Spec : ` with a space before the colon), it will not match.

**Fix:**

Inspect the raw commit message:

```bash
git log -1 --format=%B HEAD
```

Confirm the `Spec:` line looks exactly like `Spec: 2026-05-06_add-jwt-auth` (capital S, colon, single space, spec ID, nothing else on the line).

If the format differs, the `prepare-commit-msg` hook may have appended in a non-standard format. Check the hook file:

```bash
cat .git/hooks/prepare-commit-msg
```

Reinstall if needed:

```bash
specwarden git-hook uninstall
specwarden git-hook install
```

---

## `specwarden trace <commit>` prints "no Spec: trailer on this commit"

**Symptom:**

```
$ specwarden trace HEAD
commit: abc1234
no Spec: trailer on this commit.
```

**Cause:**

The commit does not have a `Spec:` line in its message. Either the `prepare-commit-msg` hook was not installed when the commit was made, or the spec was not active at commit time.

**Fix:**

This is not a bug — the commit genuinely has no spec coverage. If you want to retroactively associate the commit with a spec, amend the commit message:

```bash
git commit --amend -m "$(git log -1 --format=%s HEAD)

Spec: 2026-05-06_add-jwt-auth"
```

Note: amending a commit that has already been pushed will require a force push. Do not do this on shared branches.

---

## Hook fires but Claude Code session hangs

**Symptom:**

After wiring the hooks, Claude Code sessions become unresponsive when an edit tool is called.

**Cause:**

The hook command is blocking — it is waiting on stdin after consuming the payload, or it has entered an infinite loop. The PostToolUse hook writes to a file and exits immediately; this should not block. The most common cause is a custom shell wrapper around the hook command that waits for terminal input.

**Fix:**

Test the hook directly:

```bash
echo '{"tool_name":"Edit","tool_input":{"file_path":"x","old_string":"a","new_string":"b"}}' \
  | timeout 5 python -m specwarden.hooks.pre_tool_use
echo "exit: $?"
```

If this hangs or times out, the issue is in the hook script or its environment (e.g., a `.pth` file that triggers an interactive import). Run with `python -v` to trace imports:

```bash
echo '...' | python -v -m specwarden.hooks.pre_tool_use 2>&1 | head -50
```
