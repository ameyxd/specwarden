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
    re.compile(r"\?\s*$", re.MULTILINE),
    re.compile(r"\bdo you (?:want|need)\b", re.IGNORECASE),
    re.compile(r"\b(?:would|do) you like (?:me to)?\b", re.IGNORECASE),
    re.compile(r"\bwhich (?:approach|option|version|one)\b", re.IGNORECASE),
]


EDITING_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

# The PreToolUse deny reason, as it appears in the tool_result the model sees.
BLOCK_MARKER = "specwarden: no active spec"


@dataclass(frozen=True)
class Measurement:
    task: str
    arm: str
    wall_seconds: float
    files_modified: int
    edit_attempts: int
    blocked_edits: int
    clarification_count: int
    tool_call_count: int
    cost_usd: float
    num_turns: int
    exit_status: int


def _looks_like_question(text: str) -> bool:
    return any(p.search(text) for p in QUESTION_PATTERNS)


def _tool_result_text(block: dict) -> str:
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    return ""


def parse_jsonl(path: Path) -> tuple[int, int, float, int, int, int]:
    """Walk a session JSONL and return per-cell measurements.

    Returns: (clarification_count, tool_call_count, cost_usd, num_turns,
    edit_attempts, blocked_edits).

    `edit_attempts` and `blocked_edits` are what make the enforcement layer
    visible. `files_modified` alone cannot distinguish "the hook stopped the
    edit" from "the model never tried to edit" — both read as zero.

    The `result` event is the canonical source for cost and turn count.
    Per-event `usage` blocks are cumulative; summing them overcounts.
    """
    if not path.exists():
        return 0, 0, 0.0, 0, 0, 0

    clarifications = 0
    tool_calls = 0
    cost_usd = 0.0
    num_turns = 0
    edit_attempts = 0
    blocked_edits = 0
    seen_question_uuids: set[str] = set()

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") == "result":
            cost_usd = float(event.get("total_cost_usd") or 0.0)
            num_turns = int(event.get("num_turns") or 0)
            continue

        if event.get("type") == "user":
            content = (event.get("message", {}) or {}).get("content")
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_result":
                        continue
                    if BLOCK_MARKER in _tool_result_text(block):
                        blocked_edits += 1
            continue

        if event.get("type") != "assistant":
            continue

        msg = event.get("message", {}) or {}
        content = msg.get("content", []) or []
        if not isinstance(content, list):
            continue

        had_question = False
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "tool_use":
                tool_calls += 1
                if block.get("name") in EDITING_TOOLS:
                    edit_attempts += 1
            elif btype == "text":
                text = block.get("text") or ""
                if isinstance(text, str) and _looks_like_question(text):
                    had_question = True
        if had_question:
            uuid = event.get("uuid") or ""
            if uuid and uuid not in seen_question_uuids:
                seen_question_uuids.add(uuid)
                clarifications += 1

    return clarifications, tool_calls, cost_usd, num_turns, edit_attempts, blocked_edits


def measure(results_dir: Path) -> list[Measurement]:
    summary_path = results_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    out: list[Measurement] = []
    for entry in summary:
        log_rel = entry["log_path"]
        log_path = Path(log_rel)
        if not log_path.is_absolute():
            # The runner writes log_path relative to the project root. The
            # standard layout puts results_dir at <project>/evals/results/<X>,
            # so the project root is parents[2]. Fall back to other bases for
            # non-standard layouts (tests, custom --out, etc).
            candidates = [
                results_dir.parents[2] / log_rel if len(results_dir.parents) >= 3 else None,
                results_dir / log_rel,
                Path.cwd() / log_rel,
            ]
            for cand in candidates:
                if cand is not None and cand.exists():
                    log_path = cand
                    break
        (
            clarifications,
            tool_calls,
            cost_usd,
            num_turns,
            edit_attempts,
            blocked_edits,
        ) = parse_jsonl(log_path)
        out.append(
            Measurement(
                task=entry["task"],
                arm=entry["arm"],
                wall_seconds=float(entry["wall_seconds"]),
                files_modified=int(entry["files_modified"]),
                edit_attempts=edit_attempts,
                blocked_edits=blocked_edits,
                clarification_count=clarifications,
                tool_call_count=tool_calls,
                cost_usd=cost_usd,
                num_turns=num_turns,
                exit_status=int(entry["exit_status"]),
            )
        )
    return out


def render_scorecard(measurements: list[Measurement]) -> str:
    lines = [
        "| Task | Arm | Wall (s) | Turns | Tool calls | Edit attempts | Blocked | "
        "Files changed | Clarifications | Cost (USD) | Exit |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for m in measurements:
        lines.append(
            f"| {m.task} | {m.arm} | {m.wall_seconds:.1f} | {m.num_turns} | "
            f"{m.tool_call_count} | {m.edit_attempts} | {m.blocked_edits} | "
            f"{m.files_modified} | {m.clarification_count} | "
            f"${m.cost_usd:.4f} | {m.exit_status} |"
        )
    return "\n".join(lines) + "\n"


def render_summary(measurements: list[Measurement]) -> str:
    """Per-arm averages across all tasks."""
    by_arm: dict[str, list[Measurement]] = {}
    for m in measurements:
        by_arm.setdefault(m.arm, []).append(m)
    lines = [
        "",
        "## Per-arm averages",
        "",
        "| Arm | Wall avg (s) | Turns avg | Tool calls avg | Edit attempts | Blocked | "
        "Files changed total | Clarifications total | Cost total (USD) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in sorted(by_arm):
        cells = by_arm[arm]
        n = len(cells)
        wall_avg = sum(c.wall_seconds for c in cells) / n
        turns_avg = sum(c.num_turns for c in cells) / n
        tools_avg = sum(c.tool_call_count for c in cells) / n
        attempts_total = sum(c.edit_attempts for c in cells)
        blocked_total = sum(c.blocked_edits for c in cells)
        files_total = sum(c.files_modified for c in cells)
        clar_total = sum(c.clarification_count for c in cells)
        cost_total = sum(c.cost_usd for c in cells)
        lines.append(
            f"| {arm} | {wall_avg:.1f} | {turns_avg:.1f} | {tools_avg:.1f} | "
            f"{attempts_total} | {blocked_total} | "
            f"{files_total} | {clar_total} | ${cost_total:.4f} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render eval scorecard from a results directory.")
    parser.add_argument("results_dir", type=Path)
    parser.add_argument("--out", type=Path, help="Write the scorecard markdown to this path.")
    args = parser.parse_args(argv)

    measurements = measure(args.results_dir)
    table = render_scorecard(measurements) + render_summary(measurements)
    if args.out:
        args.out.write_text(table, encoding="utf-8")
        print(f"scorecard written to {args.out}")
    else:
        print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
