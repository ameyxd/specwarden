"""Guards on the eval harness itself.

Every bug these cover silently produced a *plausible* benchmark number rather
than an error, which is why they went unnoticed through a published result.
"""

import json
import subprocess
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parents[1] / "evals"
sys.path.insert(0, str(EVALS_DIR))
from run_eval import _claude_args, changed_files  # noqa: E402


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_claude_args_never_pass_bare(tmp_path: Path):
    """--bare is documented as "skip hooks"; it silently disabled enforcement."""
    for arm in ("A", "B", "C", "D"):
        assert "--bare" not in _claude_args(tmp_path, arm)


def test_hook_settings_are_passed_for_enforced_arms(tmp_path: Path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text("{}")
    for arm in ("C", "D"):
        assert "--settings" in _claude_args(tmp_path, arm)


def test_skill_is_withheld_from_hooks_only_arm(tmp_path: Path):
    """Arm D must not see the skill, or it predicts the block and never edits."""
    skill = tmp_path / ".claude" / "skills" / "specwarden" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# skill")
    assert "--append-system-prompt-file" not in _claude_args(tmp_path, "D")


def test_changed_files_counts_created_files(tmp_path: Path):
    """`git diff --name-only HEAD` omitted untracked files, hiding every creation."""
    _git(["init", "-q", "-b", "main"], tmp_path)
    _git(["config", "user.email", "t@t"], tmp_path)
    _git(["config", "user.name", "t"], tmp_path)
    (tmp_path / "existing.py").write_text("a\n")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-qm", "base"], tmp_path)

    (tmp_path / "brand_new.py").write_text("created by the model\n")

    assert changed_files(tmp_path) == ["brand_new.py"]


def test_changed_files_counts_modified_and_created_together(tmp_path: Path):
    _git(["init", "-q", "-b", "main"], tmp_path)
    _git(["config", "user.email", "t@t"], tmp_path)
    _git(["config", "user.name", "t"], tmp_path)
    (tmp_path / "existing.py").write_text("a\n")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-qm", "base"], tmp_path)

    (tmp_path / "existing.py").write_text("modified\n")
    (tmp_path / "brand_new.py").write_text("created\n")

    assert changed_files(tmp_path) == ["brand_new.py", "existing.py"]


def _result(task: str, arm: str, tmp_path: Path):
    from run_eval import RunResult

    return RunResult(
        task=task,
        arm=arm,
        wall_seconds=1.0,
        files_modified=0,
        files_changed=[],
        exit_status=0,
        timed_out=False,
        log_path=tmp_path / f"{task}_{arm}.jsonl",
    )


def test_summary_is_written_before_the_sweep_ends(tmp_path: Path):
    """A sweep killed partway must still be scoreable; summary.json is the index."""
    from run_eval import write_summary

    partial = [_result("task_001", "A", tmp_path)]
    path = write_summary(tmp_path, partial, "standard")

    assert len(json.loads(path.read_text())) == 1


def test_summary_rewrite_replaces_previous_contents(tmp_path: Path):
    from run_eval import write_summary

    write_summary(tmp_path, [_result("task_001", "A", tmp_path)], "standard")
    path = write_summary(
        tmp_path,
        [_result("task_001", "A", tmp_path), _result("task_001", "B", tmp_path)],
        "standard",
    )

    assert len(json.loads(path.read_text())) == 2


def test_summary_leaves_no_temp_file_behind(tmp_path: Path):
    """The atomic write must not litter, or the results dir accumulates .tmp files."""
    from run_eval import write_summary

    write_summary(tmp_path, [_result("task_001", "A", tmp_path)], "standard")

    assert list(tmp_path.glob("*.tmp")) == []
