import os
import subprocess
import sys
from pathlib import Path


def _run(cwd: Path) -> str:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[1] / "src"))
    proc = subprocess.run(
        [sys.executable, "-m", "spec_trace.hooks.session_start"],
        input="",
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_no_active_prints_reminder(tmp_path: Path):
    out = _run(tmp_path)
    assert "spec-trace" in out.lower()
    assert "no active spec" in out.lower()


def test_active_prints_id(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    (tmp_path / ".claude" / "specs" / "active").write_text("2026-05-07_demo\n")
    out = _run(tmp_path)
    assert "2026-05-07_demo" in out
