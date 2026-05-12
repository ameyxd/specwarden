#!/usr/bin/env python3
"""Eval runner for spec-trace's three-arm benchmark.

Usage examples:
    python evals/run_eval.py --task 1 --arm A
    python evals/run_eval.py --all-tasks --all-arms --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "evals" / "fixtures"
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "spec-trace"
SRC_DIR = REPO_ROOT / "src"


def _load_env_eval() -> None:
    """Load `.env.eval` (gitignored) into os.environ if present.

    Used to supply ANTHROPIC_API_KEY without exposing it in shell history
    or requiring an interactive export. Lines are KEY=VALUE; blank lines
    and `#` comments are ignored.
    """
    env_file = REPO_ROOT / ".env.eval"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _subprocess_env() -> dict[str, str]:
    """Env that guarantees spec_trace is importable from any subprocess.

    Works around a Python 3.14 + hatchling editable-install quirk where the
    .pth file is sometimes not processed. Prepending src/ to PYTHONPATH
    makes `python -m spec_trace.<X>` work regardless of install state.
    """
    _load_env_eval()
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SRC_DIR}{os.pathsep}{existing}" if existing else str(SRC_DIR)
    return env


@dataclass(frozen=True)
class RunResult:
    task: str
    arm: str
    wall_seconds: float
    files_modified: int
    exit_status: int
    log_path: Path


def discover_tasks() -> list[Path]:
    return sorted(p for p in FIXTURES.iterdir() if p.is_dir() and p.name.startswith("task_"))


def setup_workdir(fixture: Path, arm: str) -> Path:
    workdir = Path(tempfile.mkdtemp(prefix=f"spec_trace_eval_{fixture.name}_{arm}_"))
    with tarfile.open(fixture / "starting_state.tar.gz") as tar:
        tar.extractall(workdir)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=workdir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "eval@spec-trace.local"], cwd=workdir, check=True
    )
    subprocess.run(["git", "config", "user.name", "eval"], cwd=workdir, check=True)
    subprocess.run(["git", "add", "."], cwd=workdir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "starting state"], cwd=workdir, check=True)

    if arm in ("B", "C"):
        skill_dest = workdir / ".claude" / "skills" / "spec-trace"
        skill_dest.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SKILL_DIR, skill_dest, dirs_exist_ok=True)
    if arm == "C":
        subprocess.run(
            [sys.executable, "-m", "spec_trace.cli", "init", "--root", str(workdir)],
            check=True,
            env=_subprocess_env(),
        )

    return workdir


def _claude_args(workdir: Path, arm: str) -> list[str]:
    """Build the claude invocation for a given arm.

    All arms run with --bare to isolate the eval from the host's global config
    (no superpowers, no auto-discovered CLAUDE.md, no other skills). We grant
    full tool access because the workdir is an ephemeral temp directory.

    Arm-specific surface:
    - A (control): bare claude only.
    - B (advisory): skill description appended to the system prompt; no hooks.
    - C (enforced): skill description AND the workdir's .claude/settings.json,
      which wires PreToolUse / PostToolUse / SessionStart to the spec-trace hooks.
    """
    args = [
        "claude",
        "-p",
        "--bare",
        "--output-format",
        "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",
        "--add-dir",
        str(workdir),
    ]
    skill_md = workdir / ".claude" / "skills" / "spec-trace" / "SKILL.md"
    if arm in ("B", "C") and skill_md.exists():
        args.extend(["--append-system-prompt-file", str(skill_md)])
    settings = workdir / ".claude" / "settings.json"
    if arm == "C" and settings.exists():
        args.extend(["--settings", str(settings)])
    return args


def run_claude(
    workdir: Path, prompt_path: Path, log_path: Path, arm: str, dry_run: bool
) -> tuple[float, int]:
    if dry_run:
        print(f"[dry-run] would invoke claude in {workdir} with prompt {prompt_path}")
        return 0.0, 0
    prompt_text = prompt_path.read_text(encoding="utf-8")
    start = time.monotonic()
    proc = subprocess.run(
        _claude_args(workdir, arm),
        input=prompt_text,
        capture_output=True,
        text=True,
        cwd=workdir,
        env=_subprocess_env(),
    )
    elapsed = time.monotonic() - start
    log_path.write_text(proc.stdout, encoding="utf-8")
    if proc.stderr:
        (log_path.with_suffix(".stderr.txt")).write_text(proc.stderr, encoding="utf-8")
    return elapsed, proc.returncode


def files_modified(workdir: Path) -> int:
    out = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=workdir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return len([line for line in out.splitlines() if line.strip()])


def run_one(fixture: Path, arm: str, out_dir: Path, dry_run: bool) -> RunResult:
    workdir = setup_workdir(fixture, arm)
    log_path = (out_dir / f"{fixture.name}_{arm}_{int(time.time())}.jsonl").resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    elapsed, exit_status = run_claude(workdir, fixture / "prompt.md", log_path, arm, dry_run)
    return RunResult(
        task=fixture.name,
        arm=arm,
        wall_seconds=elapsed,
        files_modified=files_modified(workdir) if not dry_run else 0,
        exit_status=exit_status,
        log_path=log_path,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the spec-trace three-arm benchmark.")
    parser.add_argument("--arm", choices=["A", "B", "C"])
    parser.add_argument("--all-arms", action="store_true")
    parser.add_argument("--task", type=int)
    parser.add_argument("--all-tasks", action="store_true")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "evals" / "results" / "_local")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    args.out = args.out.resolve()

    arms = ["A", "B", "C"] if args.all_arms else [args.arm] if args.arm else None
    if not arms:
        parser.error("specify --arm or --all-arms")

    all_tasks = discover_tasks()
    if args.all_tasks:
        tasks = all_tasks
    elif args.task is not None:
        tasks = [t for t in all_tasks if t.name.startswith(f"task_{args.task:03d}_")]
        if not tasks:
            parser.error(f"no fixture found for --task {args.task}")
    else:
        parser.error("specify --task or --all-tasks")

    args.out.mkdir(parents=True, exist_ok=True)
    results: list[RunResult] = []
    for task in tasks:
        for arm in arms:
            print(f"[{arm}] {task.name} ...", flush=True)
            result = run_one(task, arm, args.out, args.dry_run)
            results.append(result)
            print(
                f"  -> {result.wall_seconds:.1f}s | "
                f"{result.files_modified} files modified | "
                f"exit={result.exit_status}"
            )

    summary_path = args.out / "summary.json"
    summary_path.write_text(
        json.dumps(
            [
                {
                    "task": r.task,
                    "arm": r.arm,
                    "wall_seconds": r.wall_seconds,
                    "files_modified": r.files_modified,
                    "exit_status": r.exit_status,
                    "log_path": (
                        str(r.log_path.relative_to(REPO_ROOT))
                        if r.log_path.is_relative_to(REPO_ROOT)
                        else str(r.log_path)
                    ),
                }
                for r in results
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nsummary written to {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
