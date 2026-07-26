"""PreToolUse hook tests.

These assert the exact wire format, not just the decision value. Claude Code
reads the decision from `hookSpecificOutput.permissionDecision`; a bare
top-level `permissionDecision` is parsed as an unknown key and ignored, which
silently disables the gate while every decision-value assertion still passes.
The shape tests below are the ones that catch that regression.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

SRC = str(Path(__file__).resolve().parents[1] / "src")


def _run(payload: dict, cwd: Path, env: dict | None = None) -> dict:
    if env is None:
        env = os.environ.copy()
    # Ensure specwarden is importable from the subprocess
    env.setdefault("PYTHONPATH", SRC)
    proc = subprocess.run(
        [sys.executable, "-m", "specwarden.hooks.pre_tool_use"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _hso(out: dict) -> dict:
    return out["hookSpecificOutput"]


# --- spec completeness ---------------------------------------------------

TEMPLATE = """# {sid}: demo

## Assumptions
What we are taking as given.

- TODO

## Scope
What this change is.

- TODO

## Non-goals
What this change is explicitly not.

- TODO

## Success criteria
How we will know we are done.

- [ ] TODO
"""

FILLED = """# demo

## Assumptions
What we are taking as given.

- calc.py is the only arithmetic module

## Scope
What this change is.

- Add subtract() to calc.py

## Non-goals
What this change is explicitly not.

- No division helper

## Success criteria
How we will know we are done.

- [ ] subtract(5, 3) returns 2
"""


def _activate(tmp_path: Path, body: str, sid: str = "2026-07-25_demo") -> None:
    specs = tmp_path / ".claude" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / f"{sid}.md").write_text(body.replace("{sid}", sid))
    (specs / "active").write_text(f"{sid}\n")


# --- wire format ---------------------------------------------------------


def test_output_nests_decision_under_hook_specific_output(tmp_path: Path):
    out = _run({"tool_name": "Read"}, cwd=tmp_path)
    assert "hookSpecificOutput" in out


def test_output_carries_hook_event_name(tmp_path: Path):
    out = _run({"tool_name": "Read"}, cwd=tmp_path)
    assert _hso(out)["hookEventName"] == "PreToolUse"


def test_decision_reason_uses_documented_key(tmp_path: Path):
    """The key is `permissionDecisionReason`, not `message`."""
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    out = _run({"tool_name": "Edit"}, cwd=tmp_path)
    assert "specwarden" in _hso(out)["permissionDecisionReason"].lower()


def test_bare_top_level_permission_decision_is_never_emitted(tmp_path: Path):
    """Regression guard: the top-level shape is silently ignored by Claude Code.

    Every branch of the hook must be free of it, so this walks all four.
    """
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    quickfix = os.environ.copy()
    quickfix["SPECWARDEN_QUICKFIX"] = "1"
    quickfix.setdefault("PYTHONPATH", SRC)
    outs = [_run({"tool_name": "Read"}, cwd=tmp_path)]
    outs.append(_run({"tool_name": "Edit"}, cwd=tmp_path))
    outs.append(_run({"tool_name": "Write"}, cwd=tmp_path, env=quickfix))
    _activate(tmp_path, FILLED)
    outs.append(_run({"tool_name": "Edit"}, cwd=tmp_path))
    _activate(tmp_path, TEMPLATE)
    outs.append(_run({"tool_name": "Edit"}, cwd=tmp_path))

    assert [o for o in outs if "permissionDecision" in o] == []


# --- decisions -----------------------------------------------------------


def test_non_editing_tool_is_allowed(tmp_path: Path):
    out = _run({"tool_name": "Read"}, cwd=tmp_path)
    assert _hso(out)["permissionDecision"] == "allow"


def test_edit_with_no_active_spec_is_denied(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    out = _run({"tool_name": "Edit"}, cwd=tmp_path)
    assert _hso(out)["permissionDecision"] == "deny"


def test_edit_with_active_spec_is_allowed(tmp_path: Path):
    _activate(tmp_path, FILLED)
    out = _run({"tool_name": "Edit"}, cwd=tmp_path)
    assert _hso(out)["permissionDecision"] == "allow"


def test_quickfix_env_overrides(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    env = os.environ.copy()
    env["SPECWARDEN_QUICKFIX"] = "1"
    env.setdefault("PYTHONPATH", SRC)
    out = _run({"tool_name": "Write"}, cwd=tmp_path, env=env)
    assert _hso(out)["permissionDecision"] == "allow"


# --- legacy compatibility ------------------------------------------------


def test_deny_also_emits_legacy_block_for_older_hosts(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    out = _run({"tool_name": "Edit"}, cwd=tmp_path)
    assert out["decision"] == "block"


def test_allow_does_not_emit_a_legacy_decision(tmp_path: Path):
    """Legacy `decision` has no allow value; emitting one would block."""
    out = _run({"tool_name": "Read"}, cwd=tmp_path)
    assert "decision" not in out


def test_untouched_template_does_not_unlock_editing(tmp_path: Path):
    """`specwarden new` + `activate` must not be a two-command bypass."""
    _activate(tmp_path, TEMPLATE)
    out = _run({"tool_name": "Edit"}, cwd=tmp_path)
    assert _hso(out)["permissionDecision"] == "deny"


def test_deny_names_the_unwritten_sections(tmp_path: Path):
    _activate(tmp_path, TEMPLATE)
    reason = _hso(_run({"tool_name": "Edit"}, cwd=tmp_path))["permissionDecisionReason"]
    assert all(s in reason for s in ("Assumptions", "Scope", "Non-goals", "Success criteria"))


def test_fully_written_spec_allows_editing(tmp_path: Path):
    _activate(tmp_path, FILLED)
    out = _run({"tool_name": "Edit"}, cwd=tmp_path)
    assert _hso(out)["permissionDecision"] == "allow"


def test_partially_written_spec_names_only_the_gaps(tmp_path: Path):
    partial = FILLED.replace("- Add subtract() to calc.py", "- TODO")
    _activate(tmp_path, partial)
    reason = _hso(_run({"tool_name": "Edit"}, cwd=tmp_path))["permissionDecisionReason"]
    assert "Scope" in reason and "Assumptions" not in reason


def test_active_pointing_at_a_missing_file_is_denied(tmp_path: Path):
    specs = tmp_path / ".claude" / "specs"
    specs.mkdir(parents=True)
    (specs / "active").write_text("2026-07-25_ghost\n")
    out = _run({"tool_name": "Edit"}, cwd=tmp_path)
    assert _hso(out)["permissionDecision"] == "deny"


def test_quickfix_still_bypasses_an_incomplete_spec(tmp_path: Path):
    """The documented escape hatch must not be blocked by the new check."""
    _activate(tmp_path, TEMPLATE)
    env = os.environ.copy()
    env["SPECWARDEN_QUICKFIX"] = "1"
    env.setdefault("PYTHONPATH", SRC)
    out = _run({"tool_name": "Edit"}, cwd=tmp_path, env=env)
    assert _hso(out)["permissionDecision"] == "allow"
