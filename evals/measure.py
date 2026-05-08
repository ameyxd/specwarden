#!/usr/bin/env python3
"""Eval measurement: turn JSONL session logs + summary.json into a scorecard.

Usage:
    python evals/measure.py evals/results/_local
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

QUESTION_PATTERNS = [
    re.compile(r"\bshould i\b", re.IGNORECASE),
    re.compile(r"\?\s*$"),
    re.compile(r"\bdo you (?:want|need)\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class Measurement:
    task: str
    arm: str
    wall_seconds: float
    files_modified: int
    clarification_count: int
    token_cost: int
    exit_status: int


def _looks_like_question(text: str) -> bool:
    return any(p.search(text) for p in QUESTION_PATTERNS)


def parse_jsonl(path: Path) -> tuple[int, int]:
    """Return (clarification_count, total_tokens)."""
    if not path.exists():
        return 0, 0
    clarifications = 0
    tokens = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            content = event.get("message", {}).get("content", [])
            for block in content if isinstance(content, list) else []:
                text = block.get("text") if isinstance(block, dict) else None
                if isinstance(text, str) and _looks_like_question(text):
                    clarifications += 1
        usage = event.get("message", {}).get("usage") or event.get("usage")
        if isinstance(usage, dict):
            tokens += int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0))
    return clarifications, tokens


def measure(results_dir: Path) -> list[Measurement]:
    summary_path = results_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    out: list[Measurement] = []
    for entry in summary:
        log_path = (results_dir.parent.parent / entry["log_path"]).resolve()
        clarifications, tokens = parse_jsonl(log_path)
        out.append(
            Measurement(
                task=entry["task"],
                arm=entry["arm"],
                wall_seconds=float(entry["wall_seconds"]),
                files_modified=int(entry["files_modified"]),
                clarification_count=clarifications,
                token_cost=tokens,
                exit_status=int(entry["exit_status"]),
            )
        )
    return out


def render_scorecard(measurements: list[Measurement]) -> str:
    lines = [
        "| Task | Arm | Wall (s) | Files mod. | Clarifications | Tokens | Exit |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for m in measurements:
        lines.append(
            f"| {m.task} | {m.arm} | {m.wall_seconds:.1f} | {m.files_modified} | "
            f"{m.clarification_count} | {m.token_cost} | {m.exit_status} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render eval scorecard from a results directory.")
    parser.add_argument("results_dir", type=Path)
    parser.add_argument("--out", type=Path, help="Write the scorecard markdown to this path.")
    args = parser.parse_args(argv)

    measurements = measure(args.results_dir)
    table = render_scorecard(measurements)
    if args.out:
        args.out.write_text(table, encoding="utf-8")
        print(f"scorecard written to {args.out}")
    else:
        print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
