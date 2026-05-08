import json
import os
import subprocess
import sys
from pathlib import Path


def _run(payload: dict, cwd: Path, env: dict | None = None) -> dict:
    if env is None:
        env = os.environ.copy()
    # Ensure spec_trace is importable from the subprocess
    env.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[1] / "src"))
    proc = subprocess.run(
        [sys.executable, "-m", "spec_trace.hooks.pre_tool_use"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_non_editing_tool_is_allowed(tmp_path: Path):
    out = _run({"tool_name": "Read"}, cwd=tmp_path)
    assert out["permissionDecision"] == "allow"


def test_edit_with_no_active_spec_is_asked(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    out = _run({"tool_name": "Edit"}, cwd=tmp_path)
    assert out["permissionDecision"] == "ask"
    assert "spec-trace" in out["message"].lower()


def test_edit_with_active_spec_is_allowed(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    (tmp_path / ".claude" / "specs" / "active").write_text("2026-05-07_demo\n")
    out = _run({"tool_name": "Edit"}, cwd=tmp_path)
    assert out["permissionDecision"] == "allow"


def test_quickfix_env_overrides(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    env = os.environ.copy()
    env["SPEC_TRACE_QUICKFIX"] = "1"
    env.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[1] / "src"))
    out = _run({"tool_name": "Write"}, cwd=tmp_path, env=env)
    assert out["permissionDecision"] == "allow"
