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
    active = tmp_path / ".claude" / "specs" / "active"

    outs = [_run({"tool_name": "Read"}, cwd=tmp_path)]
    outs.append(_run({"tool_name": "Edit"}, cwd=tmp_path))
    outs.append(_run({"tool_name": "Write"}, cwd=tmp_path, env=quickfix))
    active.write_text("2026-05-07_demo\n")
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
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    (tmp_path / ".claude" / "specs" / "active").write_text("2026-05-07_demo\n")
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
