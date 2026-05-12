import json
import os
import subprocess
import sys
from pathlib import Path


def _run(payload: dict, cwd: Path) -> None:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[1] / "src"))
    proc = subprocess.run(
        [sys.executable, "-m", "specwarden.hooks.post_tool_use"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr


def test_appends_decision_entry(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    (tmp_path / ".claude" / "decisions").mkdir(parents=True)
    (tmp_path / ".claude" / "specs" / "active").write_text("2026-05-07_demo\n")

    payload = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "src/auth/jwt.py",
            "content": "def verify(): pass\n" * 10,
        },
    }
    _run(payload, cwd=tmp_path)

    log = (tmp_path / ".claude" / "decisions" / "2026-05-07_demo.md").read_text()
    assert "src/auth/jwt.py" in log
    assert "Tool: Write" in log


def test_noop_when_no_active(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    (tmp_path / ".claude" / "decisions").mkdir(parents=True)
    payload = {"tool_name": "Write", "tool_input": {"file_path": "x.py", "content": "x"}}
    _run(payload, cwd=tmp_path)
    assert not list((tmp_path / ".claude" / "decisions").iterdir())


def test_noop_when_non_editing_tool(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    (tmp_path / ".claude" / "decisions").mkdir(parents=True)
    (tmp_path / ".claude" / "specs" / "active").write_text("2026-05-07_demo\n")

    payload = {"tool_name": "Read", "tool_input": {"file_path": "x.py"}}
    _run(payload, cwd=tmp_path)

    assert not list((tmp_path / ".claude" / "decisions").iterdir())
