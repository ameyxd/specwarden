#!/usr/bin/env python3
"""Eval runner for spec-trace's three-arm benchmark.

Usage examples:
    python evals/run_eval.py --task 1 --arm A
    python evals/run_eval.py --all-tasks --all-arms --dry-run
"""

from __future__ import annotations

import argparse
import json
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
        subprocess.run(["spec-trace", "init", "--root", str(workdir)], check=True)

    return workdir


def run_claude(
    workdir: Path, prompt_path: Path, log_path: Path, dry_run: bool
) -> tuple[float, int]:
    if dry_run:
        print(f"[dry-run] would invoke claude in {workdir} with prompt {prompt_path}")
        return 0.0, 0
    prompt_text = prompt_path.read_text(encoding="utf-8")
    start = time.monotonic()
    proc = subprocess.run(
        ["claude", "-p", "--output-format", "stream-json"],
        input=prompt_text,
        capture_output=True,
        text=True,
        cwd=workdir,
    )
    elapsed = time.monotonic() - start
    log_path.write_text(proc.stdout, encoding="utf-8")
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
    log_path = out_dir / f"{fixture.name}_{arm}_{int(time.time())}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    elapsed, exit_status = run_claude(workdir, fixture / "prompt.md", log_path, dry_run)
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
                    "log_path": str(r.log_path.relative_to(REPO_ROOT)),
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
