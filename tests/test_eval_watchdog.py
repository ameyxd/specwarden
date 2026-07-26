"""The cell watchdog.

A hung headless `claude` produces no error and no output — the sweep simply
stops advancing, which looks identical to "still working". These tests assert
the watchdog converts that into a recorded, bounded failure.
"""

import subprocess
import sys
import time
from pathlib import Path

import pytest

EVALS_DIR = Path(__file__).resolve().parents[1] / "evals"
sys.path.insert(0, str(EVALS_DIR))
import run_eval  # noqa: E402
from run_eval import TIMEOUT_EXIT, run_claude  # noqa: E402


@pytest.fixture
def prompt(tmp_path: Path) -> Path:
    p = tmp_path / "prompt.md"
    p.write_text("do the thing")
    return p


def _stub_claude(monkeypatch, script: str) -> None:
    """Replace the claude invocation with a python script we control."""
    monkeypatch.setattr(run_eval, "_claude_args", lambda wd, arm: [sys.executable, "-c", script])
    monkeypatch.setattr(run_eval, "_subprocess_env", dict)


def test_hanging_cell_is_killed_and_reported(monkeypatch, tmp_path: Path, prompt: Path):
    _stub_claude(monkeypatch, "import time; time.sleep(600)")
    log = tmp_path / "out.jsonl"

    elapsed, exit_status, timed_out = run_claude(
        tmp_path, prompt, log, "A", dry_run=False, cell_timeout=2
    )

    assert (timed_out, exit_status) == (True, TIMEOUT_EXIT)
    assert elapsed < 60


def test_watchdog_kills_orphaned_grandchildren(monkeypatch, tmp_path: Path, prompt: Path):
    """Killing only the direct child leaves grandchildren holding the pipes.

    The read then never returns and the watchdog hangs anyway, which is the
    failure mode `start_new_session` + killpg exists to prevent.
    """
    marker = tmp_path / "grandchild_alive.txt"
    script = (
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-c', "
        f"\"import time,pathlib; pathlib.Path(r'{marker}').write_text('x'); time.sleep(600)\"])\n"
        "time.sleep(600)\n"
    )
    _stub_claude(monkeypatch, script)

    _, _, timed_out = run_claude(tmp_path, prompt, tmp_path / "o.jsonl", "A", False, cell_timeout=3)

    assert timed_out
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if marker.exists():
            break
        time.sleep(0.2)
    assert marker.exists(), "grandchild never started; test would pass vacuously"
    # The whole process group must be gone, not just the direct child.
    survivors = subprocess.run(
        ["pgrep", "-f", "grandchild_alive"], capture_output=True, text=True
    ).stdout.strip()
    assert survivors == ""


def test_partial_transcript_survives_a_timeout(monkeypatch, tmp_path: Path, prompt: Path):
    """A timed-out cell must still leave something to diagnose."""
    _stub_claude(
        monkeypatch,
        'import sys, time; sys.stdout.write(\'{"type":"system"}\\n\'); '
        "sys.stdout.flush(); time.sleep(600)",
    )
    log = tmp_path / "out.jsonl"

    run_claude(tmp_path, prompt, log, "A", dry_run=False, cell_timeout=2)

    assert "system" in log.read_text()


def test_fast_cell_is_not_flagged(monkeypatch, tmp_path: Path, prompt: Path):
    _stub_claude(monkeypatch, 'print(\'{"type":"result"}\')')

    _, exit_status, timed_out = run_claude(
        tmp_path, prompt, tmp_path / "o.jsonl", "A", dry_run=False, cell_timeout=30
    )

    assert (timed_out, exit_status) == (False, 0)
