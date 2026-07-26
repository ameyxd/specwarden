import json
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parents[1] / "evals"
sys.path.insert(0, str(EVALS_DIR))
from measure import measure, parse_jsonl, render_scorecard  # noqa: E402


def test_parse_jsonl_counts_questions(tmp_path: Path):
    log = tmp_path / "session.jsonl"
    events = [
        {
            "type": "assistant",
            "uuid": "u1",
            "message": {"content": [{"type": "text", "text": "Done."}]},
        },
        {
            "type": "assistant",
            "uuid": "u2",
            "message": {"content": [{"type": "text", "text": "Should I also rename the file?"}]},
        },
        {
            "type": "assistant",
            "uuid": "u3",
            "message": {"content": [{"type": "text", "text": "Working on it"}]},
        },
        {
            "type": "result",
            "total_cost_usd": 0.42,
            "num_turns": 4,
        },
    ]
    log.write_text("\n".join(json.dumps(e) for e in events))

    clarifications, tool_calls, cost, turns, _, _ = parse_jsonl(log)

    assert clarifications == 1
    assert tool_calls == 0
    assert cost == 0.42
    assert turns == 4


def test_parse_jsonl_counts_tool_calls(tmp_path: Path):
    log = tmp_path / "session.jsonl"
    events = [
        {
            "type": "assistant",
            "uuid": "u1",
            "message": {
                "content": [
                    {"type": "tool_use", "name": "Edit"},
                    {"type": "text", "text": "applying the edit"},
                ]
            },
        },
        {
            "type": "assistant",
            "uuid": "u2",
            "message": {"content": [{"type": "tool_use", "name": "Bash"}]},
        },
        {"type": "result", "total_cost_usd": 0.1, "num_turns": 2},
    ]
    log.write_text("\n".join(json.dumps(e) for e in events))

    _, tool_calls, _, _, _, _ = parse_jsonl(log)

    assert tool_calls == 2


def test_parse_jsonl_handles_missing_result(tmp_path: Path):
    log = tmp_path / "session.jsonl"
    log.write_text(json.dumps({"type": "user", "message": {}}) + "\n")

    clarifications, tool_calls, cost, turns, _, _ = parse_jsonl(log)

    assert clarifications == 0
    assert tool_calls == 0
    assert cost == 0.0
    assert turns == 0


def test_measure_assembles_summary(tmp_path: Path):
    nested = tmp_path / "evals" / "results" / "_local"
    nested.mkdir(parents=True)
    log = nested / "task_001_A_111.jsonl"
    log.write_text(json.dumps({"type": "result", "total_cost_usd": 0.5, "num_turns": 7}) + "\n")
    (nested / "summary.json").write_text(
        json.dumps(
            [
                {
                    "task": "task_001_demo",
                    "arm": "A",
                    "wall_seconds": 12.5,
                    "files_modified": 3,
                    "exit_status": 0,
                    "log_path": f"evals/results/_local/{log.name}",
                }
            ]
        )
    )

    measurements = measure(nested)

    assert len(measurements) == 1
    m = measurements[0]
    assert m.task == "task_001_demo"
    assert m.arm == "A"
    assert m.wall_seconds == 12.5
    assert m.files_modified == 3
    assert m.cost_usd == 0.5
    assert m.num_turns == 7


def test_render_scorecard_table_shape():
    from measure import Measurement

    rows = [
        Measurement(
            task="task_001_demo",
            arm="A",
            wall_seconds=10.0,
            files_modified=2,
            timed_out=False,
            edit_attempts=1,
            blocked_edits=1,
            clarification_count=0,
            tool_call_count=5,
            cost_usd=0.1234,
            num_turns=4,
            exit_status=0,
        )
    ]
    table = render_scorecard(rows)
    assert "| Task | Arm | Wall (s) | Turns |" in table
    assert "task_001_demo" in table
    assert "$0.1234" in table


def test_parse_jsonl_counts_edit_attempts(tmp_path: Path):
    """Edit attempts separate "the hook stopped it" from "it never tried"."""
    log = tmp_path / "session.jsonl"
    events = [
        {
            "type": "assistant",
            "uuid": "u1",
            "message": {
                "content": [
                    {"type": "tool_use", "name": "Edit"},
                    {"type": "tool_use", "name": "Bash"},
                    {"type": "tool_use", "name": "Write"},
                ]
            },
        },
        {"type": "result", "total_cost_usd": 0.1, "num_turns": 1},
    ]
    log.write_text("\n".join(json.dumps(e) for e in events))

    _, _, _, _, edit_attempts, _ = parse_jsonl(log)

    assert edit_attempts == 2


def test_parse_jsonl_counts_blocked_edits(tmp_path: Path):
    log = tmp_path / "session.jsonl"
    events = [
        {
            "type": "assistant",
            "uuid": "u1",
            "message": {"content": [{"type": "tool_use", "name": "Edit"}]},
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "content": (
                            "specwarden: no active spec. Run `/spec <slug>` first to "
                            "define what you're building before editing files."
                        ),
                    }
                ]
            },
        },
        {"type": "result", "total_cost_usd": 0.1, "num_turns": 2},
    ]
    log.write_text("\n".join(json.dumps(e) for e in events))

    _, _, _, _, edit_attempts, blocked = parse_jsonl(log)

    assert (edit_attempts, blocked) == (1, 1)


def test_parse_jsonl_reads_blocks_from_structured_tool_results(tmp_path: Path):
    """tool_result content arrives as a list of blocks, not only as a string."""
    log = tmp_path / "session.jsonl"
    events = [
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "specwarden: no active spec. Run `/spec <slug>` first "
                                    "to define what you're building before editing files."
                                ),
                            }
                        ],
                    }
                ]
            },
        },
        {"type": "result", "total_cost_usd": 0.1, "num_turns": 1},
    ]
    log.write_text("\n".join(json.dumps(e) for e in events))

    _, _, _, _, _, blocked = parse_jsonl(log)

    assert blocked == 1


def test_unblocked_edit_is_not_counted_as_blocked(tmp_path: Path):
    log = tmp_path / "session.jsonl"
    events = [
        {
            "type": "assistant",
            "uuid": "u1",
            "message": {"content": [{"type": "tool_use", "name": "Edit"}]},
        },
        {
            "type": "user",
            "message": {
                "content": [{"type": "tool_result", "content": "has been updated successfully"}]
            },
        },
        {"type": "result", "total_cost_usd": 0.1, "num_turns": 2},
    ]
    log.write_text("\n".join(json.dumps(e) for e in events))

    _, _, _, _, edit_attempts, blocked = parse_jsonl(log)

    assert (edit_attempts, blocked) == (1, 0)


def test_measure_defaults_timed_out_for_older_summaries(tmp_path: Path):
    """summary.json files written before the watchdog existed lack the field."""
    nested = tmp_path / "evals" / "results" / "_local"
    nested.mkdir(parents=True)
    log = nested / "t_A_1.jsonl"
    log.write_text(json.dumps({"type": "result", "total_cost_usd": 0.1, "num_turns": 1}) + "\n")
    (nested / "summary.json").write_text(
        json.dumps(
            [
                {
                    "task": "t",
                    "arm": "A",
                    "wall_seconds": 1.0,
                    "files_modified": 0,
                    "exit_status": 0,
                    "log_path": f"evals/results/_local/{log.name}",
                }
            ]
        )
    )

    assert measure(nested)[0].timed_out is False


def test_session_start_banner_is_not_counted_as_a_block(tmp_path: Path):
    """The banner shares a prefix with the deny reason but is not an enforcement event."""
    banner = (
        "specwarden: no active spec. Run `/spec <slug>` to define what you're building.\n"
        "  Spec template sections: Assumptions, Scope, Non-goals, Success criteria.\n"
    )
    log = tmp_path / "session.jsonl"
    events = [
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": banner}]}},
        {"type": "result", "total_cost_usd": 0.1, "num_turns": 1},
    ]
    log.write_text("\n".join(json.dumps(e) for e in events))

    _, _, _, _, _, blocked = parse_jsonl(log)

    assert blocked == 0


def test_real_deny_reason_is_still_counted(tmp_path: Path):
    deny = (
        "specwarden: no active spec. Run `/spec <slug>` first to define "
        "what you're building before editing files."
    )
    log = tmp_path / "session.jsonl"
    events = [
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": deny}]}},
        {"type": "result", "total_cost_usd": 0.1, "num_turns": 1},
    ]
    log.write_text("\n".join(json.dumps(e) for e in events))

    _, _, _, _, _, blocked = parse_jsonl(log)

    assert blocked == 1
